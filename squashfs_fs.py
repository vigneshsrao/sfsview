import struct
import zlib
import lzma
import io
import math
import time
from typing import List, Dict, Tuple, Optional, BinaryIO
from squashfs import SquashFSSuperblock, CompressionID

def get_rwx(a):
    val = ""
    if a & 4:
        val+='r'
    else:
        val+='-'
    if a & 2:
        val+='w'
    else:
        val+='-'
    if a & 1:
        val+='x'
    else:
        val += '-'
    return val

def get_perm(perm):
    val = ""
    val+=get_rwx((perm & 0b111000000) >> 6)
    val+=get_rwx((perm & 0b000111000) >> 3)
    val+=get_rwx((perm & 0b111))
    return val

# Constants for inode types
class InodeType:
    DIRECTORY = 1
    FILE = 2
    SYMLINK = 3
    BLOCK_DEVICE = 4
    CHAR_DEVICE = 5
    FIFO = 6
    SOCKET = 7

class DataBlock:
    def __init__(self, compressed_data: bytes, uncompressed_size: int):
        self.compressed_data = compressed_data
        self.uncompressed_size = uncompressed_size

class Fragment:
    def __init__(self, index: int, offset: int, size: int):
        self.index = index
        self.offset = offset
        self.size = size

class InodeHeader:
    def __init__(self, inode_header):

        self.typ = inode_header[0];
        self.perms = inode_header[1];
        self.uid = inode_header[2]
        self.gid = inode_header[3]
        self.mtime = inode_header[4]
        self.inode_num = inode_header[5]

    def typestr(self):
        if self.typ == InodeType.DIRECTORY:
            return "DIRECTORY (Type 1)"
        if self.typ == InodeType.FILE:
            return "FILE (Type 2)"
        if self.typ == InodeType.SYMLINK:
            return "SYMLINK (Type 3)"
        if self.typ == InodeType.BLOCK_DEVICE:
            return "BLOCK_DEVICE (Type 4)"
        if self.typ == InodeType.CHAR_DEVICE:
            return "CHAR_DEVICE (Type 5)"
        if self.typ == InodeType.FIFO:
            return "FIFO (Type 6)"
        if self.typ == InodeType.SOCKET:
            return "SOCKET (Type 7)"

    def print(self):

        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.mtime))
        perms = get_perm(self.perms);
        print("Inode Header:")
        print("-------------")
        print(f"Type:         {self.typestr()}");
        print(f"Perms:        {perms} ( {self.perms} )");
        print(f"uid idx:      {self.uid}");
        print(f"gid idx:      {self.gid}");
        print(f"mtime:        {date_str} (Timestamp: {self.mtime})");
        print(f"inode_num:    {self.inode_num}");

class FileInode:
    def __init__(self, inode_header, block_start, frag_idx, block_offset, file_size):
        self.header = InodeHeader(inode_header);
        self.block_start = block_start;
        self.frag_idx = frag_idx;
        self.block_offset = block_offset;
        self.file_size = file_size;

    def print(self):

        self.header.print();
        print("FILE Inode Entry:")
        print("-----------------")
        print(f"Block Start:  {self.block_start}")
        print(f"Frag Index :  {self.frag_idx}")
        print(f"Block Offset: {self.block_offset}");
        print(f"Size:         {self.file_size}");
        print("")

class DirInode:
    def __init__(self, inode_header, block_idx, link_count, file_size, block_offset, parent):
        self.header = InodeHeader(inode_header);
        self.block_idx = block_idx;
        self.link_count = link_count;
        self.file_size = file_size;
        self.block_offset = block_offset;
        self.parent = parent;

    def print(self):
        self.header.print();
        print("DIR Inode Entry:")
        print("-----------------")
        print(f"Block Start:  {self.block_idx}")
        print(f"Link Count :  {self.link_count}")
        print(f"Size:         {self.file_size}");
        print(f"Block Offset: {self.block_offset}");
        print(f"Parent:       {self.parent}");
        print("")


class FragmentEntry:

    def __init__(self, start, size):
        self.start = start

        uncompressed = False
        if ((size >> 24) & 1) == 1:
            uncompressed = True

        self.size = size & ~(1 << 24)
        self.uncompressed = uncompressed

    def print(self):

        print("Fragment Entry")
        print("--------------")
        print(f"Start:         {hex(self.start)}")
        print(f"Size:          {hex(self.size)}")
        print(f"Uncompressed:  {str(self.uncompressed)}")


class FragmentBlock:

    def __init__(self, entries):
        self.entries = entries

    def print(self):

        print("Fragment Block");
        print("--------------");
        for i in range(0, len(self.entries)):
            print(f"Index:     {i}")
            print(f"---------------")
            entry = self.entries[i]
            entry.print()

class SquashFSParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file = open(file_path, 'rb')
        self.superblock = None
        self.root_inode = None
        self.id_table = []
        self.current_directory = None
        self.inodes = []
        self.fragment_table = []
        
        # Read superblock first
        self._read_superblock()

        if self.superblock:
            # Read ID table
            self._read_id_table()

            self.parse_inode_table()
            self.parse_fragment_table()
            # Read root inode
            # self._read_root_inode()
           
            # Set current directory to root
            self.current_directory = self.root_inode
    
    def __del__(self):
        if hasattr(self, 'file') and self.file:
            self.file.close()
    
    def _read_superblock(self):
        # Reset file position
        self.file.seek(0)
        superblock_data = self.file.read(96)
        
        # Use unpack_squashfs_superblock from squashfs.py
        from squashfs import unpack_squashfs_superblock
        self.superblock = unpack_squashfs_superblock(superblock_data)
    
    def _read_id_table(self):
        if not self.superblock:
            return
        
        # Go to id table start
        self.file.seek(self.superblock.id_table_start)
        
        # Read id table - this is a simplified implementation
        # In reality, the id table is more complex with compression
        self.id_table = []
        for i in range(self.superblock.id_count):
            id_data = self.file.read(4)
            id_value = struct.unpack("<I", id_data)[0]
            self.id_table.append(id_value)

    def parse_inode_dir(self, header, data):

        dirdata = struct.unpack("<IIHHI", data[:16]);


        fd = DirInode(inode_header=header,
                       block_idx=dirdata[0],
                       link_count = dirdata[1],
                       file_size=dirdata[2],
                       block_offset = dirdata[3],
                       parent = dirdata[4]);

        self.inodes.append(fd)

        return 32


    def parse_inode_file(self, header, data):


        # typ = inode_header[0];
        # perms = inode_header[1];
        # uid = inode_header[2]
        # gid = inode_header[3]
        # mtime = inode_header[4]
        # inode_num = inode_header[5]

        filedata = struct.unpack("<IIII", data[:16]);
        block_start = filedata[0]
        frag_idx = filedata[1]
        block_offset = filedata[2]
        file_size = filedata[3]

        block_size = self.superblock.block_size;

        num_blocks = 0

        if frag_idx == 0xFFFFFFFF:
            num_blocks = math.ceil(file_size / block_size)
        else:
            num_blocks = math.floor(file_size / block_size)


        fd = FileInode(inode_header=header,
                       block_start=block_start,
                       frag_idx = frag_idx,
                       block_offset = block_offset,
                       file_size=file_size);
        # print(f"Block Start: {block_start}")
        # print(f"Frag Index : {frag_idx}")
        # print(f"Block Offset: {block_offset}");
        # print(f"Size: {file_size}");
        # print(f"Num Blocks: {num_blocks}");

        self.inodes.append(fd)

        return 16 + num_blocks*4 + 16


    def parse_decompressed_inode_table(self, data):

        start = 0

        while(start+16 < len(data)) :

            inode_header = struct.unpack("<HHHHII", data[start:start+16])

            typ = inode_header[0];

            if typ == InodeType.FILE:
                start += self.parse_inode_file(inode_header, data[start+16:])
            elif typ == InodeType.DIRECTORY:
                start += self.parse_inode_dir(inode_header, data[start+16:])
            else:
                print(f"ERROR: Unsupported file type {typ}")
                exit(-1)

    def get_metadata(self, offset):


        self.file.seek(offset)
        size = self.file.read(2)

        # First 2 bytes store the size
        size = struct.unpack("<H", size)[0];

        uncompressed = False;
        if size & 0x8000:
            uncompressed = True;
            size = size & ~0x8000


        data = self.file.read(size);
        if uncompressed:
            return data

        return self._decompress_block(data);


    def parse_fragment_block(self, data):
        block = []
        for i in range(0, len(data), 16):
            start = struct.unpack("<Q", data[i:i+8])[0]
            size  = struct.unpack("<I", data[i+8:i+12])[0]
            entry = FragmentEntry(start, size)
            block.append(entry)

        return FragmentBlock(block)


    def parse_fragment_table(self):

        if not self.superblock:
            return

        print("Parsing fragment table @ "+hex(self.superblock.fragment_table_start))
        print("Size: "+hex(self.superblock.fragment_entry_count))
        size = self.superblock.fragment_entry_count
        self.file.seek(self.superblock.fragment_table_start);
        tab = self.file.read(size*8);
        table = [struct.unpack("<Q", tab[i:i+8])[0] for i in range(0, size*8, 8)]

        for entry in table:
            print(entry)
            metadata = self.get_metadata(entry);
            block = self.parse_fragment_block(metadata);
            self.fragment_table.append(block)

    def parse_inode_table(self):
        if not self.superblock:
            return

        print("Parsing inode table @ "+hex(self.superblock.inode_table_start))
        self.file.seek(self.superblock.inode_table_start);
        data = self.file.read(2);
        size = struct.unpack("<H", data)[0];
        inode_data = self.file.read(size);
        inode_data = self._decompress_block(inode_data, 12)

        # print(inode_data, len(inode_data))

        self.parse_decompressed_inode_table(inode_data)

    def _decompress_block(self, compressed_data: bytes, uncompressed_size: int) :
        if not self.superblock:
            return b''
        
        compression_id = self.superblock.compression_id
        
        if compression_id == CompressionID.GZIP:
            return zlib.decompress(compressed_data)
        elif compression_id == CompressionID.LZMA:
            raise NotImplementedError("lzma decompression not implemented")
        elif compression_id == CompressionID.XZ:
            raise NotImplementedError("XZ decompression not implemented")
        elif compression_id == CompressionID.LZ4:
            raise NotImplementedError("LZ4 decompression not implemented")
        elif compression_id == CompressionID.ZSTD:
            raise NotImplementedError("ZSTD decompression not implemented")
        else:
            raise ValueError(f"Unsupported compression method: {compression_id}")
    
    # def change_directory(self, path):
    #     """Change the current directory"""
    #     # Simplified implementation - would need path traversal logic
    #     if path == "/":
    #         self.current_directory = self.root_inode
    #         return True
    #     elif path in self.current_directory.children:
    #         child = self.current_directory.children[path]
    #         if child.inode_type == InodeType.DIRECTORY:
    #             self.current_directory = child
    #             return True
    #     return False

    # def get_file_content(self, filename):
    #     """Get the content of a file"""
    #     # Simplified implementation - would need file content reading logic
    #     if self.current_directory and filename in self.current_directory.children:
    #         file_inode = self.current_directory.children[filename]
    #         if file_inode.inode_type == InodeType.FILE:
    #             content = b''
    #             # Read data blocks
    #             for block in file_inode.blocks:
    #                 content += self._decompress_block(block.compressed_data, block.uncompressed_size)

    #             # Read fragment if present
    #             if file_inode.fragment:
    #                 # Would need to fetch and decompress fragment
    #                 pass

    #             return content[:file_inode.size]  # Trim to file size
    #     return b''
