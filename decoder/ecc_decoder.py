"""
ECCDecoder module for the DataVideoCodec Decoder.

Applies Reed-Solomon error correction decoding to recover
the original data from a potentially corrupted bitstream.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from reedsolo import RSCodec, ReedSolomonError
from core.constants import RS_CODEWORD_SIZE
from core.utils import get_logger

logger = get_logger("ECCDecoder")

# Minimum blocks needed before parallelism is worthwhile
_PARALLEL_THRESHOLD = 32


def _decode_batch(nsym, blocks_batch):
    """Decode a batch of RS blocks in a worker thread.
    
    Returns list of (decoded_data, num_errors, is_correctable) tuples.
    """
    codec = RSCodec(nsym)
    k = RS_CODEWORD_SIZE - nsym
    results = []
    for block in blocks_batch:
        try:
            decoded = codec.decode(block)
            decoded_data = bytes(decoded[0])
            num_errors = len(decoded[2]) if len(decoded) > 2 else 0
            results.append((decoded_data, num_errors, True))
        except ReedSolomonError:
            raw_data = block[:k]
            results.append((bytes(raw_data), -1, False))
    return results


class ECCDecoder:
    """Reed-Solomon ECC decoder.

    Decodes ECC-encoded data in blocks, correcting errors within
    the RS code's correction capacity and flagging uncorrectable blocks.
    """

    @staticmethod
    def _compute_nsym(overhead: float) -> int:
        """Compute the number of ECC parity symbols per codeword."""
        nsym = int(RS_CODEWORD_SIZE * overhead)
        nsym = max(2, min(nsym, RS_CODEWORD_SIZE - 1))
        return nsym

    @staticmethod
    def decode(ecc_data: bytes, overhead: float):
        """Apply Reed-Solomon decoding to ECC-encoded data.

        Uses multithreading for large block counts to maximize throughput
        while remaining safe for GUI environments.

        Args:
            ecc_data: ECC-encoded byte data (concatenated codewords).
            overhead: ECC overhead fraction used during encoding.

        Returns:
            Tuple of (corrected_bytes, error_stats).
        """
        nsym = ECCDecoder._compute_nsym(overhead)
        codeword_size = RS_CODEWORD_SIZE

        # Split data into blocks
        blocks = []
        for i in range(0, len(ecc_data), codeword_size):
            blocks.append(ecc_data[i:i + codeword_size])

        total_blocks = len(blocks)

        # Choose parallel vs sequential based on block count
        if total_blocks >= _PARALLEL_THRESHOLD:
            # Split blocks into batches for each worker
            num_workers = min(os.cpu_count() or 4, 8)
            batch_size = max(1, total_blocks // num_workers)
            
            # Create batches
            batches = [
                blocks[i:i + batch_size]
                for i in range(0, total_blocks, batch_size)
            ]

            all_results = [None] * len(batches)
            
            # Use ThreadPoolExecutor for GUI safety (no process fork/spawn issues)
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = {
                    executor.submit(_decode_batch, nsym, batch): idx
                    for idx, batch in enumerate(batches)
                }
                for future in as_completed(futures):
                    idx = futures[future]
                    all_results[idx] = future.result()
            
            # Flatten results keeping order
            flat_results = []
            for batch_result in all_results:
                flat_results.extend(batch_result)
            all_results = flat_results
        else:
            # Sequential for small block counts
            all_results = _decode_batch(nsym, blocks)

        # Aggregate results in order
        decoded_chunks = []
        error_stats = {
            "total_blocks": total_blocks,
            "errors_corrected": 0,
            "uncorrectable_blocks": 0,
            "block_errors": [],
        }

        for decoded_data, num_errors, is_correctable in all_results:
            decoded_chunks.append(decoded_data)
            if is_correctable:
                error_stats["errors_corrected"] += num_errors
                error_stats["block_errors"].append(num_errors)
            else:
                error_stats["uncorrectable_blocks"] += 1
                error_stats["block_errors"].append(-1)
                logger.warning(
                    f"Block {len(error_stats['block_errors'])}: uncorrectable RS error"
                )

        corrected_bytes = b"".join(decoded_chunks)

        logger.info(
            f"ECC decoded: {len(ecc_data)} bytes -> {len(corrected_bytes)} bytes | "
            f"Blocks: {total_blocks}, "
            f"Corrected: {error_stats['errors_corrected']} errors, "
            f"Uncorrectable: {error_stats['uncorrectable_blocks']} blocks"
        )

        return corrected_bytes, error_stats
