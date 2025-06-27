import pytest
from loguru import logger
import sys
import inspect # For inspect.currentframe()
from io import StringIO

from bibliofabric.log_config import configure_logging

def test_configure_logging_default_level_and_sink():
    """Test configure_logging with default INFO level and stderr sink."""
    logger.remove() # Ensure clean state
    initial_handlers_count = len(logger._core.handlers)

    configure_logging() # Defaults to INFO and sys.stderr

    assert len(logger._core.handlers) == initial_handlers_count + 1
    # Last added handler is the one we configured
    handler_id = list(logger._core.handlers.keys())[-1]
    handler = logger._core.handlers[handler_id]

    assert handler._levelno == logger.level("INFO").no
    # Checking sink is tricky as it's a complex object.
    # We can infer it by checking if a log message goes to stderr (default)
    # or by checking the type if possible, but direct comparison is hard.
    # For this test, we'll trust the default sink parameter.

    # Test logging output
    logger.info("Test INFO message from default config")
    # (visual check or more complex stream capture needed for content)


def test_configure_logging_custom_level_debug():
    """Test configure_logging with a custom DEBUG level."""
    logger.remove()
    configure_logging(level="DEBUG")
    handler_id = list(logger._core.handlers.keys())[-1]
    handler = logger._core.handlers[handler_id]
    assert handler._levelno == logger.level("DEBUG").no
    logger.debug("Test DEBUG message")


def test_configure_logging_custom_level_warning():
    """Test configure_logging with a custom WARNING level."""
    logger.remove()
    configure_logging(level="WARNING")
    handler_id = list(logger._core.handlers.keys())[-1]
    handler = logger._core.handlers[handler_id]
    assert handler._levelno == logger.level("WARNING").no
    logger.warning("Test WARNING message")


def test_configure_logging_custom_sink_stringio():
    """Test configure_logging with a custom StringIO sink."""
    logger.remove()
    string_io_sink = StringIO()
    configure_logging(sink=string_io_sink, level="INFO")

    handler_id = list(logger._core.handlers.keys())[-1]
    handler = logger._core.handlers[handler_id]

    # Check if the sink is our StringIO object by trying to write to it
    # and checking its content. Loguru wraps sinks, so direct comparison
    # of handler._sink might not work as expected or be straightforward.
    log_message = "Test message to StringIO"
    logger.info(log_message)

    logged_output = string_io_sink.getvalue()
    # Check that the raw message is there
    assert log_message in logged_output
    # Check that the level INFO is part of the formatted log for that message
    # This is a bit brittle if the format changes drastically, but good for now.
    # The log_message is emitted from line 65 of this file.
    assert f"INFO     | test_log_config:test_configure_logging_custom_sink_stringio:65 - {log_message}" in logged_output

def test_configure_logging_removes_existing_handlers():
    """Test that configure_logging removes pre-existing handlers."""
    logger.remove()
    # Add a dummy handler first
    dummy_sink = lambda _: None
    logger.add(dummy_sink, level="ERROR")
    assert len(logger._core.handlers) == 1

    configure_logging(level="INFO") # This should remove the dummy handler

    assert len(logger._core.handlers) == 1 # Only the new one should exist
    handler_id = list(logger._core.handlers.keys())[-1]
    handler = logger._core.handlers[handler_id]
    assert handler._levelno == logger.level("INFO").no


@pytest.fixture(autouse=True)
def reset_logger_after_test():
    """Fixture to reset Loguru to a default state after each test in this module."""
    yield
    logger.remove()
    logger.add(sys.stderr, level="INFO") # Restore a basic default handler
