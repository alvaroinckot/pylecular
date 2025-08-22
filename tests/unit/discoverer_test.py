"""Unit tests for the discoverer module."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from pylecular.discoverer import Discoverer


class TestDiscoverer:
    """Test Discoverer class."""

    @pytest.fixture
    def mock_transit(self):
        """Create a mock transit."""
        transit = AsyncMock()
        transit.beat = AsyncMock()
        return transit

    @pytest.fixture
    def mock_broker(self, mock_transit):
        """Create a mock broker."""
        broker = Mock()
        broker.transit = mock_transit
        broker.logger = Mock()
        return broker

    @pytest.mark.asyncio
    async def test_discoverer_initialization(self, mock_broker):
        """Test Discoverer initialization."""
        discoverer = Discoverer(mock_broker)

        assert discoverer.broker == mock_broker
        assert discoverer.transit == mock_broker.transit
        assert isinstance(discoverer._tasks, list)
        assert len(discoverer._tasks) == 1  # Should have heartbeat task
        assert discoverer._tasks[0].get_name() == "discoverer-heartbeat"

    @pytest.mark.asyncio
    async def test_discoverer_heartbeat_interval(self, mock_broker):
        """Test that discoverer uses correct heartbeat interval."""
        assert Discoverer.HEARTBEAT_INTERVAL == 5.0

    @pytest.mark.asyncio
    async def test_discoverer_periodic_beat(self, mock_broker, mock_transit):
        """Test that discoverer sends periodic heartbeats."""
        # Create discoverer with shorter interval for testing
        original_interval = Discoverer.HEARTBEAT_INTERVAL
        Discoverer.HEARTBEAT_INTERVAL = 0.1  # 100ms for fast testing

        try:
            discoverer = Discoverer(mock_broker)

            # Wait for a few heartbeats
            await asyncio.sleep(0.35)  # Should allow for 3+ beats

            # Stop the discoverer
            await discoverer.stop()

            # Check that beat was called multiple times
            assert mock_transit.beat.call_count >= 2

        finally:
            # Restore original interval
            Discoverer.HEARTBEAT_INTERVAL = original_interval

    @pytest.mark.asyncio
    async def test_discoverer_stop(self, mock_broker):
        """Test discoverer stop method."""
        discoverer = Discoverer(mock_broker)

        # Verify task is running
        assert len(discoverer._tasks) == 1
        assert not discoverer._tasks[0].done()

        # Stop discoverer
        await discoverer.stop()

        # Verify task was cancelled and list is cleared
        assert len(discoverer._tasks) == 0

    @pytest.mark.asyncio
    async def test_discoverer_stop_with_no_tasks(self, mock_broker):
        """Test discoverer stop when no tasks are running."""
        discoverer = Discoverer(mock_broker)

        # Clear tasks manually to simulate no tasks
        discoverer._tasks.clear()

        # Should not raise any errors
        await discoverer.stop()

        assert len(discoverer._tasks) == 0

    @pytest.mark.asyncio
    async def test_discoverer_stop_with_completed_tasks(self, mock_broker):
        """Test discoverer stop with already completed tasks."""
        discoverer = Discoverer(mock_broker)

        # Cancel and wait for task to complete
        for task in discoverer._tasks:
            task.cancel()

        # Wait a bit for cancellation to take effect
        await asyncio.sleep(0.01)

        # Stop should handle completed tasks gracefully
        await discoverer.stop()

        assert len(discoverer._tasks) == 0

    @pytest.mark.asyncio
    async def test_discoverer_heartbeat_error_handling(self, mock_broker, mock_transit):
        """Test that heartbeat errors are handled gracefully."""
        # Make beat method raise an error
        mock_transit.beat.side_effect = RuntimeError("Network error")

        # Shorter interval for testing
        original_interval = Discoverer.HEARTBEAT_INTERVAL
        Discoverer.HEARTBEAT_INTERVAL = 0.05

        try:
            discoverer = Discoverer(mock_broker)

            # Wait for a few attempted beats
            await asyncio.sleep(0.2)

            # Stop the discoverer
            await discoverer.stop()

            # Check that error was logged
            mock_broker.logger.error.assert_called()
            error_message = str(mock_broker.logger.error.call_args[0][0])
            assert "Error in periodic beat" in error_message
            assert "Network error" in error_message

        finally:
            Discoverer.HEARTBEAT_INTERVAL = original_interval

    @pytest.mark.asyncio
    async def test_discoverer_heartbeat_with_broker_without_logger(self, mock_transit):
        """Test heartbeat error handling when broker has no logger."""
        # Create broker without logger attribute
        broker = Mock()
        broker.transit = mock_transit
        # Explicitly don't set logger attribute

        # Make beat method raise an error
        mock_transit.beat.side_effect = RuntimeError("Test error")

        original_interval = Discoverer.HEARTBEAT_INTERVAL
        Discoverer.HEARTBEAT_INTERVAL = 0.05

        try:
            discoverer = Discoverer(broker)

            # Wait for error to occur
            await asyncio.sleep(0.1)

            # Stop the discoverer
            await discoverer.stop()

            # Should not raise any errors even without logger

        finally:
            Discoverer.HEARTBEAT_INTERVAL = original_interval

    @pytest.mark.asyncio
    async def test_discoverer_multiple_instances(self, mock_broker):
        """Test that multiple discoverer instances work independently."""
        discoverer1 = Discoverer(mock_broker)
        discoverer2 = Discoverer(mock_broker)

        # Each should have their own tasks
        assert len(discoverer1._tasks) == 1
        assert len(discoverer2._tasks) == 1
        assert discoverer1._tasks[0] != discoverer2._tasks[0]

        # Stop both
        await discoverer1.stop()
        await discoverer2.stop()

        # Both should be empty
        assert len(discoverer1._tasks) == 0
        assert len(discoverer2._tasks) == 0

    @pytest.mark.asyncio
    async def test_discoverer_stop_timeout_handling(self, mock_broker):
        """Test that stop handles timeout gracefully."""
        discoverer = Discoverer(mock_broker)

        # Create a task that doesn't respond to cancellation quickly
        async def stubborn_task():
            try:
                while True:
                    await asyncio.sleep(10)  # Long sleep
            except asyncio.CancelledError:
                # Simulate slow cleanup
                await asyncio.sleep(2)  # Longer than stop timeout
                raise

        # Replace the heartbeat task with our stubborn task
        for task in discoverer._tasks:
            task.cancel()
        await asyncio.sleep(0.01)
        discoverer._tasks.clear()

        stubborn = asyncio.create_task(stubborn_task())
        discoverer._tasks.append(stubborn)

        # Stop should complete even if task doesn't finish in timeout
        await discoverer.stop()

        # Tasks list should be cleared regardless
        assert len(discoverer._tasks) == 0

        # Clean up the stubborn task
        stubborn.cancel()
        try:
            await stubborn
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_discoverer_task_naming(self, mock_broker):
        """Test that discoverer tasks are properly named."""
        discoverer = Discoverer(mock_broker)

        assert len(discoverer._tasks) == 1
        assert discoverer._tasks[0].get_name() == "discoverer-heartbeat"

        await discoverer.stop()

    @pytest.mark.asyncio
    async def test_discoverer_cancellation_during_beat(self, mock_broker, mock_transit):
        """Test that cancellation during beat is handled properly."""

        # Make beat take some time
        async def slow_beat():
            await asyncio.sleep(1)

        mock_transit.beat = slow_beat

        original_interval = Discoverer.HEARTBEAT_INTERVAL
        Discoverer.HEARTBEAT_INTERVAL = 0.1

        try:
            discoverer = Discoverer(mock_broker)

            # Wait for first beat to start
            await asyncio.sleep(0.15)

            # Stop while beat is in progress
            await discoverer.stop()

            # Should complete without errors
            assert len(discoverer._tasks) == 0

        finally:
            Discoverer.HEARTBEAT_INTERVAL = original_interval
