from os.path import getsize
from struct import pack, unpack
import numpy as np

holo_header_version = 4
holo_header_size = 64
holo_header_padding_size = 35

struct_format = (
    '='
    '4s'
    'H'                 # unsigned short Version number
    'H'                 # unsigned short number of bits per pixels
    'I'                 # unsigned int width of image
    'I'                 # unsigned int height of image
    'I'                 # unsigned int number of images
    'Q'                 # unsigned long long total data size
    'B'                 # unsigned char endianness
)

class HoloFile:
    def __init__(self, path: str, header: (int, int, int, int)):
        self.width = header[0]
        self.height = header[1]
        self.bytes_per_pixel = header[2]
        self.nb_images = header[3]
        self.path = path

class FileReader(HoloFile):
    def __init__(self, path: str):
        self.path = path
        self.io = open(path, 'rb')
        header_bytes = self.io.read(holo_header_size - holo_header_padding_size)
        self.io.read(holo_header_padding_size)

        holo, _version, bits_per_pixel, w, h, img_nb, _data_size, _endianness = unpack(struct_format, header_bytes)
        if holo.decode('ascii') != "HOLO":
            self.io.close()
            raise Exception('Cannot read holo file')

        header = (w, h, int(bits_per_pixel / 8), img_nb)
        HoloFile.__init__(self, path, header)

    def get_all(self) -> bytes:
        data_total_size = self.nb_images * self.height * self.width * self.bytes_per_pixel
        self.io.seek(0)
        h = self.io.read(holo_header_size)
        c = self.get_all_frames()
        f = self.io.read(getsize(self.path) - holo_header_size - data_total_size)
        return h, c, f

    def get_all_frames(self) -> bytes:
        frame_size = self.height * self.width * self.bytes_per_pixel
        frame_res = self.height * self.width
        if self.bytes_per_pixel == 1:
            data_type = np.uint8
        elif self.bytes_per_pixel == 2:
            data_type = np.uint16
        frame_batch = np.zeros((frame_res, self.nb_images), dtype = data_type) 
        for i in range(self.nb_images): 
            self.update_loading_bar(i, self.nb_images)
            self.io.seek(holo_header_size + frame_size * i)
            data = self.io.read(frame_size)
            for j in range(frame_res):
                if self.bytes_per_pixel == 1:
                    frame_batch[j,i] = data[j] 
                elif self.bytes_per_pixel == 2:
                    frame_batch[j,i] = (data[j * 2]) + (data[j * 2 + 1] << 8)        
        return frame_batch   
    
    def update_loading_bar(self, index: int, total: int):
        if index == total - 1:
            print("\r[..........] 100.00%")
            return
        bar_index = float((index / total))
        print("\r[", end='')
        print('.' * int(bar_index * 10), end='')
        print(' ' * (10 - int(bar_index * 10)), end='')
        print('] ' + "%.2f" % (round(bar_index * 100, 2)) + '%', end='', flush=True)

    def close(self):
        self.io.close()

class FileWriter(HoloFile):
    def __init__(self, path: str, header: (int, int, int, int), data: bytes):
        HoloFile.__init__(self, path, header)
        self.io = open(path, 'wb')
        self.data = data

    def write(self):
        h = pack(struct_format,
                b'HOLO',
                holo_header_version,
                self.bytes_per_pixel * 8,
                self.width,
                self.height,
                self.nb_images,
                self.width * self.height * self.nb_images * self.bytes_per_pixel,
                1)
        self.io.write(h) # header
        self.io.write(pack(str(holo_header_padding_size) + "s", b'0')) # padding
        self.io.write(self.data) # data
        self.io.write(pack("2s", b'{}')) # empty json footer

    def close(self):
        self.io.close()