# NDDataFile3D.py
# NDDataFile 3D python class
# NDI data file to handle 3D data

# import ndtrack
from ndtrack.datafile.NDDataFile import *


class NDDataFile3D(NDDataFile):

    def __init__(self, filename=None, file_format=NDDataFileFormat.UNKNOWN):
        super().__init__(filename, file_format)
        self._header = f"Frame,X,Y,Z\n"

    def initialize(self, num_items):
        """ @override NDDataFile::initialize
            A 3D data file contains n items, each with 3 floating point subitems: x, y, z
        """
        if num_items > 1:
            self._header = f"Frame"
            for i in range(1, num_items + 1):
                self._header += f",X_{i},Y_{i},Z_{i}"
        else:
            self._header = f"Frame,X,Y,Z"

        return super().initialize(num_items)

    def _do_write_data_csv(self, data):
        """ @override NDDataFile::_do_write_data_csv
            Write one frame of 3D data in CSV format

            Parameters:
            data    list of NDPosition
        """
        self._file.write(str(self._cur_frame))
        for pos in data:
            self._file.write(",{}".format(pos.csv()))
        self._file.write("\n")

    def _do_read_frame_csv(self):
        """ @override NDDataFile::_do_read_frame_csv
            Read one frame of data from CSV file
            Data format is:
                Frame, X_1, Y_1, Z_1, ... , X_n, Y_n, Z_n
        """
        # read next line from file
        line = self._file.readline()
        # split csv file
        values = line.split(',')
        # the first value is the Frame number
        frame_number = int(values[0])

        i = 1
        data3d = []
        while i < len(values) - 1:
            # X, Y, Z, err
            x = float(values[i])
            y = float(values[i+1])
            z = float(values[i+2])
            data3d.append(NDPosition(x, y, z))
            i += 3
        return frame_number, data3d

    def _do_verify_data(self, data):
        """ @override NDDataFile::_do_verify_data
        """
        if not isinstance(data, list):
            raise NDError(NDStatusCode.FILE_ERROR, "Data must be provided in a list", self)
        if not isinstance(data[0], NDPosition):
            raise NDError(NDStatusCode.FILE_ERROR, "Data must be provided in a list of NDPosition", self)
        if len(data) != self._num_items:
            raise NDError(NDStatusCode.FILE_ERROR, "Number of items does not match number of items in file", self)


def sample_n3d_write(filename):
    """ sample method to write 3D data to a NDDataFile3D """
    # list of positions to use during the example (4 markers)
    positions = [NDPosition(1, 2, 3),
                 NDPosition(1.1, 2.2, 3.3),
                 NDPosition(11.11, 22.22, 33.33),
                 NDPosition(111.111, 222.222, 333.333)]

    # create the data file object
    f = NDDataFile3D(filename)

    # initialize the data file to contain n items
    f.initialize(len(positions))
    f.set_comment("NDDataFile3D Sample")

    # open the data file for writing
    f.open_write()

    # write 5 frames of data, changing the positions by a small amount each frame
    for frame in range(5):
        # move each marker slightly each frame
        delta = NDPosition(0.001 * frame, 0.002 * frame, 0.003 * frame)
        data = [pos + delta for pos in positions]
        f.write(data)

    # close the data file
    f.close()


def sample_n3d_read(filename):
    """ sample method for reading 3D data from an NDDataFile3D """
    # create the data file object
    f = NDDataFile3D(filename)

    # open file for reading
    f.open_read()

    # read data until the end of file
    file_end = False
    while not file_end:
        # read one frame of data
        frame_number, data3d = f.read_frame()

        # when the end of the file is reached, read_frame returns None
        file_end = frame_number is None

        # log the frame of data
        if not file_end:
            logging.log(NDLogLevel.Test, "Frame {}".format(frame_number))
            for pos in data3d:
                logging.log(NDLogLevel.Test, pos)

    # close the data file
    f.close()


def main():
    # set up to log everything
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : %(levelname)s : %(message)s')

    try:
        # write data to 3D CSV file
        sample_n3d_write("out/nddatafile_3d.csv")
        # read data from 3D CSV file
        sample_n3d_read("out/nddatafile_3d.csv")
    except NDError as err:
        logging.error(err)


if __name__ == "__main__":
    main()
