from lib.core_utils.common import YggdrasilUtilities as Ygg

from lib.core_utils.logging_utils import custom_logger

logging = custom_logger(__name__.split(".")[-1])


# def get_last_processed_seq() -> str:
#     """Retrieve the last processed sequence number from a file.

#     Returns:
#         str: The last processed sequence number.
#     """
#     seq_file = Ygg.get_path(".last_processed_seq")

#     if seq_file.is_file():
#         with open(seq_file, "r") as file:
#             return file.read().strip()
#     else:
#         # Otherwise return a default sequence value of your choice.
#         # NOTE: Zero (0) means start from the beginning. Note ideal!
#         # TODO: Read default sequence value from configuration file.
#         default_since = 0
#         return default_since


# def save_last_processed_seq(last_processed_seq: str) -> None:
#     """Save the last processed sequence number to a file.

#     Args:
#         last_processed_seq (str): The last processed sequence number to save.
#     """
#     seq_file = Ygg.get_path(".last_processed_seq")

#     with open(seq_file, "w") as file:
#         file.write(last_processed_seq)