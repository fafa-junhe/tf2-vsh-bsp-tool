import os

from . import bsp

# When adjusting offsets, the following data items need to be taken care of:
# - Each lump's offset in the lump table
# - The offset held in each directory entry in the game lump

def __aligned_offset(offset):
	return ((offset - 1) + (4 - ((offset - 1) % 4))) if offset > 0 else 0

def __compute_lump_ordering_by_offset(bsp_file):
	lumps = []

	for index in range(0, bsp.LUMP_TABLE_NUM_ENTRIES):
		(offset, length, _, _) = bsp.get_lump_descriptor(bsp_file, index)
		lumps.append((offset, length, index))

	lumps.sort(key=lambda item: item[0])
	return [item[2] for item in lumps]

def __shift_lump(bsp_file, lump_index, delta):
	(offset, size, version, lzma_flags) = bsp.get_lump_descriptor(bsp_file, lump_index)
	lump_data = bsp.get_lump_data(bsp_file, lump_index)

	bsp_file.seek(offset + delta)
	bsp_file.write(lump_data)

	bsp.set_lump_descriptor(bsp_file, lump_index, offset + delta, size, version, lzma_flags)

def adjust_offsets_after_lump(bsp_file, delta, lump_index: int):
	if delta == 0:
		return

	ordered_lumps = __compute_lump_ordering_by_offset(bsp_file)

	# After manual experimentation, the following seems to be true for TF2:
	# - The final two lumps by offset are 35 (gamelumps) and 40 (pakfile)
	# - Each gamelump is included immediately after the gamelumps listing,
	#   before the pakfile lump begins.
	# This means we can deal with all lumps up to the last two,
	# and then cater for those separately.
	ordered_lumps = ordered_lumps[:-2]

	if delta > 0:
		delta = __aligned_offset(delta)
		print(f"Adjusting BSP lump offsets by {delta} bytes (with alignment) to accommodate new entities lump")

		# First adjust most of the lumps:
		for index in ordered_lumps:
			__shift_lump(bsp_file, index, delta)

		# TODO: Then deal with the edge cases
		raise NotImplementedError()
	else:
		ordered_lumps.reverse()
		delta = -1 * __aligned_offset(-delta)
		print(f"Adjusting BSP lump offsets by {delta} bytes (with alignment) to accommodate new entities lump")

		# TODO: First deal with the edge cases
		raise NotImplementedError()

		# Then adjust the other lumps:
		for index in ordered_lumps:
			__shift_lump(bsp_file, index, delta)

		# Finally, trim the file
		bsp_file.seek(delta, os.SEEK_END)
		bsp_file.truncate()