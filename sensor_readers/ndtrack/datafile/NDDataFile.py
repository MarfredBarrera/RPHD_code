# NDDataFile.py
# NDDataFile python class
# An NDDataFile is a generic data file handler.
# NDI data is written in frames with a file descriptor.

# import standard libraries
import struct
import time
import os.path

# import ndtrack
from ndtrack.ndtypes.NDDataTypes import *


class NDDataFileFormat(IntEnum):
    """ NDDataFileFormat enumerator
        List of supported data file formats
    """
    UNKNOWN = 0
    # CSV data is written in ASCII format
    CSV = 1


class NDDataFileMode(IntEnum):
    """ NDDataFileMode enumator
        File modes: READ, WRITE
    """
    UNKNOWN = 0
    READ = 1
    WRITE = 2


class NDDataFile:
    """ NDDataFile
        A data file used by NDI
        Examples of data file formats are csv.
        Examples of data file contents are 3D, Pose, 6D.
        NDI Data Files inherit from this class.
    """

    def __init__(self, filename=None, file_format=NDDataFileFormat.UNKNOWN):
        """
        Create an NDDataFile. The filename and format can be specified at initialization, or added later.

        Args:
            filename: name of the file to use
            file_format: file format can be specified if it is not the default. format is implied by file extension:
                .csv -> CSV
        """
        # full name of the file, including path
        self._filename = None
        # file format: CSV or ascii CUSTOM
        self._format = None
        # indicates if the file is initialized
        self._is_init = False
        # indicates file mode: Read or Write
        self._mode = NDDataFileMode.UNKNOWN
        # file object
        self._file = None
        # number of frames in the file
        self._num_frames = 0
        # current frame number, 1-indexed
        self._cur_frame = 1
        self._frame_number = None

        # update the file format
        self._set_format(file_format)
        # update the name of the file
        self.set_filename(filename)

        # CSV information
        self._header = "Frame,Data"

    def __str__(self):
        """ Print information about the the NDDataFile """
        return f"{self.filename} [{self._format.name}|{self._is_init}|{self.is_open}|{self._mode}] " \
               f"({self._cur_frame} of {self._num_frames})"

    @property
    def filename(self) -> str:
        """ Return the filename of the file """
        return self._filename

    @property
    def is_open(self):
        """ Indicate if the data file is open """
        return (self._file is not None) and (not self._file.closed)

    @property
    def format(self):
        """ Return the format of the file """
        if self._format == NDDataFileFormat.UNKNOWN:
            self._determine_format()
        return self._format

    @property
    def num_frames(self):
        """ Return the number of frames in the file """
        return self._num_frames

    @property
    def mode(self):
        """ Return the file mode: Read or Write """
        return self._mode

    @property
    def is_csv(self):
        """ Indicates if the file is in CSV format """
        return self.format == NDDataFileFormat.CSV

    def set_filename(self, filename):
        """ Update the filename to the one specified

        Args:
            filename: file name to use

        Returns:
            format (CSV) being used, implied by the filename
        """
        # update the filename associated with this DataFile
        if filename is not None:
            self._filename = filename

        self._determine_format()

        return True

    def _set_format(self, file_format):
        """ Used to specify the file format

        Args:
            file_format: specifies the file format
        """
        # update file format
        self._format = file_format

        # return the newly specified file format
        return self._format

    def _determine_format(self):
        """ Determine the file format based on the filename.
            Files with standard extensions can be treated in the appropiate format.
                .csv -> CSV file format
        """
        # if the format is already specified, nothing to do
        if self._format != NDDataFileFormat.UNKNOWN:
            return self._format

        # if no filename has been specified, the format is UNKNOWN
        if self.filename is None:
            return NDDataFileFormat.UNKNOWN

        # get the file extension
        root, ext = os.path.splitext(self.filename)
        if ext == ".csv":
            return self._set_format(NDDataFileFormat.CSV)

        # unable to determine file format from the filename
        return self._set_format(NDDataFileFormat.UNKNOWN)

    def open_write(self, filename=None, header=None):
        """ Open the file for writing
            If the filename is not specified, it is expected that it has been
            previously specified. Otherwise, it is an error.

        Args:
            filename: name of the file to open for writing
            header: custom header

        Returns:
            True if successful
        """
        # if the file is already open, nothing to do
        if self.is_open:
            raise NDError(NDStatusCode.FILE_ERROR, "File is already open", self)

        # use the specified filename
        self.set_filename(filename)

        # ensure that filename has been specified
        if self.filename is None:
            raise NDError(NDStatusCode.FILE_ERROR, "Filename not specified", self)

        # open data file for writing
        logging.info(f"Opening {self.filename} for writing")

        # if the file is not initialized, cannot proceed
        if not self._is_init:
            raise NDError(NDStatusCode.FILE_ERROR, f"File is not initialized: {self.filename}", self)

        # create destination folder, if necessary
        path = os.path.dirname(self.filename)
        if path != "":
            try:
                os.mkdir(path)
            except FileExistsError:
                # path already exists, everything is OK
                pass

        self._file = open(self.filename, 'w')

        # update header, if one is specified
        if header is not None:
            self._header = header

        # write the file header
        try:
            self._file.write(f"{self._header}\n")
        except Exception as err:
            raise NDError(NDStatusCode.FILE_ERROR, "Error while writing ASCII file header", self) from err

        # update file status
        self._mode = NDDataFileMode.WRITE
        self._num_frames = 0

        return True

    def _read_header(self):
        """ Read the file header and initialize file accordingly """
        # the first line is the header
        header = self._file.readline()
        self._first_line = len(header) + 1

        # count the number of frames
        self._num_frames = 0
        for _ in self._file:
            self._num_frames += 1
        self._file.seek(self._first_line)

    def open_read(self, filename=None):
        """ Open the specified file for reading
            If the filename is not specified, it is expected that it has been
            previously specified. Otherwise, it is an error.

        Args:
            filename    [optional] Name of the file to open for reading
        """
        # if the file is already open, raise an error
        if self.is_open:
            raise NDError(NDStatusCode.FILE_ERROR, "File is already open", self)

        # use the specified filename
        self.set_filename(filename)

        # if no filename has been specified, raise an error
        if self.filename is None:
            raise NDError(NDStatusCode.FILE_ERROR, "Filename not specified", self)

        # open data file for reading
        logging.info(f"Opening {self.filename} for reading")
        self._file = open(self.filename, 'r')

        # update file status
        self._mode = NDDataFileMode.READ

        # read the file header
        self._read_header()
        return True

    def initialize(self, items):
        """ Initialize the file to contain the specified data.
            This is used in preparation of opening the file for writing.

        Args:
            items       number of items in each frame of data

        Returns:
            True if successful
        """
        # if the file is already initialized, raise an error
        if self.is_open:
            raise NDError(NDStatusCode.FILE_ERROR, "File is already open", self)

        # store the file parameters
        #self._num_items = items

        # update the file status
        self._is_init = True
        return True

    def close(self):
        """ Close the data file """
        # if the file is not open, there is nothing to do
        if not self.is_open:
            return True

        # close data file
        logging.info(f"Closing {self.filename}")
        self._file.close()

        # update file status
        self.__init__(None, NDDataFileFormat.UNKNOWN)
        return True

    def set_comment(self, comment: str = "NDTrack"):
        """ Update the file comment

        Args:
            comment: comment to write when writing NDFP files

        Returns:
            True if successful
        """
        self._comment = comment
        return True

    def set_frequency(self, freq: float = 1.0):
        """ Update frame frequency at which the data was collected

        Args:
            freq: frequency to write when writing NDFP files

        Returns:
            True if successful
        """
        self._frequency = freq
        return True

    def _do_write_data_csv(self, data):
        """ Write the data to CSV file.
            Subclasses must override this method to write data in thier specific format
        """
        # write the data to file
        if isinstance(data, list) or isinstance(data, tuple):
            # convert the list to a comma separated string
            csv = ','.join(str(v) for v in data)
            csv += "\n"
            # write the completed string to file
            return self._do_write_data_csv(csv)

        # write data directly to file
        try:
            if data[-1] != "\n":
                data += "\n"
            self._file.write(data)
        except Exception as err:
            raise NDError(NDStatusCode.FILE_ERROR, "Error writing to file", self) from err

    def _advance_frame(self, data):
        # advance to the next frame
        self._num_frames += 1
        self._cur_frame += 1
        self._subitems_written = 0

    def write(self, data, frame_number=None):
        """ Write the specified data to file.
        The data is interpreted and written based on the file type

        Args:
            data: data to write to file
            frame_number: frame number to write to file

        Returns:
            True if successful
        """

        # ensure that the file is open
        if not self.is_open:
            raise NDError(NDStatusCode.FILE_ERROR, "File is not open", self)
        # ensure that the file is open for writing
        if self.mode != NDDataFileMode.WRITE:
            raise NDError(NDStatusCode.FILE_ERROR, "File is not open for writing", self)

        # if no data has been provided, raise an error
        if data is None:
            raise NDError(NDStatusCode.USE_ERROR, "Data for writing has not been provided", self)

        self._frame_number = frame_number

        # perform data write
        try:
            # write the data to csv
            self._do_write_data_csv(data)
            # determine if a full frame of data was written
        except NDError as err:
            raise NDError(NDStatusCode.FILE_ERROR, f"Error while writing to file {self.filename}", self) from err

        self._advance_frame(data)

        return True

    def _do_read_frame_csv(self):
        line = self._file.readline()  # read next line from file
        part = line.partition(',')  # split the CSV data
        frame_number = part[0]  # the first value is the frame_number
        data = part[2][:-1]  # the remainder of the string is the data
        return int(frame_number), data

    def read_frame(self, loop=False):
        """ Read one frame of data from the file

        Args:
            loop: indicates if reading should re-start at the top of the file when EOF is encountered

        Returns:
            frame_number, data: the frame number and data for the next frame read from file
        """
        # ensure that the file is open
        if not self.is_open:
            raise NDError(NDStatusCode.FILE_ERROR, "File is not open", self)
        # ensure that the file is open for reading
        if self.mode != NDDataFileMode.READ:
            raise NDError(NDStatusCode.FILE_ERROR, "File is not open for reading", self)

        # if reading beyond the end of the file
        if self._cur_frame > self._num_frames:
            if loop:
                # if caller requests to loop, start again at the top of the file
                self._file.seek(self._first_line)
                self._cur_frame = 1
            else:
                # if caller is going through the file once, indicate EOF reached
                return None, None

        frame_number = None
        data = None
        frame_number, data = self._do_read_frame_csv()
        self._cur_frame += 1  # advance to the next frame

        return frame_number, data


def sample_csv():
    """ use NDDataFile to write a simple CSV ascii data file"""

    try:
        # create output NDDataFile. assumes ascii due to csv extension
        file_name = "out/nddatafile.csv"
        csv_file = NDDataFile()
        csv_file.initialize( 1 )

        # write data to CSV file
        # open file for writing
        csv_file.open_write(file_name)

        # write data using string
        csv_file.write("1,1.111,2.222,3.333\n")

        # write data using list
        csv_file.write([2, 11.111, 22.222, 33.333])

        # write data using tuple
        csv_file.write((3, 111.111, 222.222, 333.333))

        # close file
        csv_file.close()

        # read data from CSV file
        # open file for reading
        asc_read = NDDataFile(file_name)
        asc_read.open_read(file_name)

        # read data until the end of the file
        while True:
            # read each frame of data. each frame contains a frame number followed by data
            frame_number, data = asc_read.read_frame()

            # when the end of the file is reached, read_frame returns None
            if frame_number is None:
                break

            # log the data read from file
            logging.info(f"Frame {frame_number}: {data}")

        # close file
        asc_read.close()

    except NDError as err:
        logging.error(err)

def main():
    # set up to log everything
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : %(levelname)s : %(message)s')

    try:
        # execute sample code for NDDataFiles in each of the accepted formats
        sample_csv()
    except NDError as err:
        logging.error(err)


if __name__ == "__main__":
    main()
