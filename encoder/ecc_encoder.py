"""
ECCEncoder module for the DataVideoCodec Encoder.

Applies Reed-Solomon error correction coding to data bytes,
producing ECC-protected byte blocks that can survive lossy
compression errors.
"""

from reedsolo import RSCodec
from core.constants import RS_CODEWORD_SIZE
from core.utils import get_logger

logger = get_logger("ECCEncoder")


class ECCEncoder:
    """Reed-Solomon ECC encoder.

    Encodes data in blocks using RS(255, k) codes where k depends
    on the desired ECC overhead percentage.
    """

    @staticmethod
    def _compute_nsym(overhead: float) -> int:
        """Compute the number of ECC parity symbols per codeword.

        For an RS(255, k) code, nsym = 255 - k = number of parity symbols.
        The overhead percentage determines nsym relative to the codeword:
            At 10% overhead: nsym ≈ 25, k = 230
            At 20% overhead: nsym ≈ 51, k = 204
            At 40% overhead: nsym ≈ 102, k = 153

        Args:
            overhead: ECC overhead as a fraction (0.1, 0.2, or 0.4).

        Returns:
            Number of parity symbols (nsym).
        """
        nsym = int(RS_CODEWORD_SIZE * overhead)
        # Ensure nsym is at least 2 (minimum for RS to be useful)
        nsym = max(2, min(nsym, RS_CODEWORD_SIZE - 1))
        return nsym

    @staticmethod
    def encode(data: bytes, overhead: float) -> bytes:
        """Apply Reed-Solomon encoding to data.

        Data is processed in blocks of k bytes, where k = 255 - nsym.
        Each block produces a 255-byte codeword (k data + nsym parity).

        Args:
            data: Raw data bytes to encode.
            overhead: ECC overhead as a fraction (0.1, 0.2, or 0.4).

        Returns:
            ECC-encoded bytes (concatenated codewords).
        """
        nsym = ECCEncoder._compute_nsym(overhead)
        codec = RSCodec(nsym)
        k = RS_CODEWORD_SIZE - nsym  # data bytes per codeword

        encoded_chunks = []
        total_blocks = (len(data) + k - 1) // k

        for i in range(0, len(data), k):
            block = data[i:i + k]
            encoded_block = bytes(codec.encode(block))
            encoded_chunks.append(encoded_block)

        result = b"".join(encoded_chunks)
        logger.info(
            f"ECC encoded: {len(data)} bytes -> {len(result)} bytes "
            f"(nsym={nsym}, k={k}, blocks={total_blocks}, overhead={overhead*100:.0f}%)"
        )
        return result

    @staticmethod
    def get_block_size(overhead: float) -> int:
        """Get the data block size (k) for a given overhead.

        Args:
            overhead: ECC overhead fraction.

        Returns:
            Number of data bytes per RS codeword block.
        """
        nsym = ECCEncoder._compute_nsym(overhead)
        return RS_CODEWORD_SIZE - nsym
