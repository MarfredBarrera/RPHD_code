# NDDataFile6D.py
# NDDataFile 6D python class
# NDI data file to handle 6D data

# import ndtrack
from ndtrack.datafile.NDDataFile import *


class NDDataFile6D(NDDataFile):

    def __init__(self, filename=None, file_format=NDDataFileFormat.UNKNOWN):
        super().__init__(filename, file_format)
        self._header = f"Frame,q0,qx,qy,qz,X,Y,Z,err\n"

    def initialize(self, num_items):
        """ @override NDDataFile::initialize
            A 6D data file contains n items, each with 8 floating point subitems: q0, qx, qy, qz, X, Y, Z, error
        """
        if num_items > 1:
            self._header = f"Frame"
            for i in range(1, num_items + 1):
                self._header += f",q0_{i},qx_{i},qy_{i},qz_{i},X_{i},Y_{i},Z_{i},err_{i}"
        else:
            self._header = f"Frame,q0,qx,qy,qz,X,Y,Z,err"

        return super().initialize(num_items)

    def _do_write_data_csv(self, data):
        """ @override NDDataFile::_do_write_data_csv
            Write one frame of 6D data in CSV format

            Parameters:
            data    list of NDPose
        """
        if self._frame_number is None:
            self._file.write(str(self._cur_frame))
        else:
            self._file.write(str(self._frame_number))
        for pose in data:
            self._file.write(",{}".format(pose.csv()))
        self._file.write("\n")

    def _do_read_frame_csv(self):
        """ @override NDDataFile::_do_read_frame_csv
            Read one frame of data from CSV file
            Data format is:
                Frame, q0_1, qx_1, qy_1, qz_1, x_1, y_1, z_1, err_1, ... , q0_n, qx_n, qy_n, qz_n, x_n, y_n, z_n, err_n
        """
        # read next line from file
        line = self._file.readline()
        # split csv file
        values = line.split(',')
        # the first value is the Frame number
        frame_number = int(values[0])

        i = 1
        data6d = []
        while i < len(values) - 1:
            # q0, qx, qy, qz, x, y, z, err
            q0 = float(values[i+0])
            qx = float(values[i+1])
            qy = float(values[i+2])
            qz = float(values[i+3])
            x = float(values[i+4])
            y = float(values[i+5])
            z = float(values[i+6])
            err = float(values[i+7])
            data6d.append(NDPose(NDPosition(x, y, z), NDRotation(q0, qx, qy, qz), err))
            i += 8
        return frame_number, data6d

    def _do_verify_data(self, data):
        """ @override NDDataFile::_do_verify_data
        """
        if not isinstance(data, list):
            raise NDError(NDStatusCode.FILE_ERROR, "Data must be provided in a list", self)
        if len(data) != self._num_items:
            raise NDError(NDStatusCode.FILE_ERROR, f"Number of items ({len(data)}) "
                                                   f"does not match number of items in file ({self._num_items})", self)
        if (self._num_items > 0) and not isinstance(data[0], NDPose):
            raise NDError(NDStatusCode.FILE_ERROR, "Data must be provided in a list of NDPosition", self)


def write_file(filename):
    """ generic method to write 6D data to a NDDataFile6D
    """
    # list of positions to use during the example
    poses = [NDPose(NDPosition(1, 11, 111),
                    NDRotation(0.1, 0.01, 0.001, 0.01), 1),
             NDPose(NDPosition(2, 22, 222),
                    NDRotation(0.2, 0.02, 0.002, 0.02), 2)]

    # create the data file object
    f = NDDataFile6D(filename)

    # initialize the data file to contain n items
    f.initialize(len(poses))
    f.set_comment("NDDataFile6D Sample")

    # open the data file for writing
    f.open_write()

    # write 5 frames of data, changing the positions by a small amount each frame
    for frame in range(5):
        delta = NDPosition(0.001 * frame, 0.002 * frame, 0.003 * frame)
        r_delta = NDRotation(0.1 * frame, 0.2 * frame, 0.3 * frame, 0.4 * frame)
        data = [NDPose(pose.pos + delta, pose.rot * r_delta, pose.meas_err) for pose in poses]
        f.write(data)

    # close the data file
    f.close()


def read_file(filename):
    """ generic method for reading 6D data from an NDDataFile6D
    """
    # create the data file object
    f = NDDataFile6D(filename)

    # open file for reading
    f.open_read()

    # read data until the end of file
    while True:
        # read one frame of data
        frame_number, data6d = f.read_frame()
        # when the end of the file is reached, read_frame returns None
        if frame_number is None:
            break

        # log the frame of data
        logging.log(NDLogLevel.Test, "Frame {}".format(frame_number))
        for pos in data6d:
            logging.log(NDLogLevel.Test, pos)

    # close the data file
    f.close()


def main():
    # set up to log everything
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : %(levelname)s : %(message)s')

    try:
        # write data to 6D CSV file
        write_file("out/nddatafile_6d.csv")
        # read data from 6D CSV file
        read_file("out/nddatafile_6d.csv")
    except NDError as err:
        logging.error(err)


if __name__ == "__main__":
    main()
