import ij.*;
import ij.io.*;
import ij.plugin.*;
import java.io.*;
import java.nio.*;

/**
 *  Opens .holo image sequences.
 *
 *  A holo file contains a header, raw data and a footer.
 *  The header speficy how raw data are formatted and the footer provide information about digital hologram rendering parameters.
 *
 *  Find more at: https://ftp.espci.fr/incoming/Atlan/holovibes/holo/HoloFileSpecification.pdf
 */

public class Read_Holo extends ImagePlus implements PlugIn
{
    private String  plugin_name = "Read Holo";
    private int     max_header_size = 64;   // Max header size in holo file
    private int     nb_frame_pixel;         // Number of pixel in a frame (equals to: width * height)
    private int     frame_size;             // Size in bytes of a frame (equals to: width * height * bit_depth)
    private int     batch_read = 64;        // Number of images to read per read() call

    // Header variables
    private int     magic_number;           // Magic number, always set to "HOLO"
    private int     version;                // Version of holo file
    private int     bit_depth;              // Bit depth of raw data
    private int     width;                  // Width of a frame
    private int     height;                 // Height of a frame
    private int     num_frames;             // Total number of frames in raw data
    private long    data_size;              // Total raw data size (always equals to width * height * num_frames * (bit_depth / 8))
    private int     endianness;             // Endianness of raw data


    public void run(String arg)
    {
        // Open dialog for file selection
        OpenDialog  od = new OpenDialog("Open a .holo file...", arg);

        String      directory = od.getDirectory();
        String      filename = od.getFileName();
        String      path = directory + filename;

        InputStream is;
        ImageStack  stack;

        if (filename == null)
            return;

        IJ.showStatus("Opening: " + path);
        try
        {
            if ((is = new FileInputStream(path)) == null)
                return ;
            if ((stack = createStack(is)) == null)
            {
                is.close();
                return ;
            }
            is.close();
            setStack(filename, stack);
            show();
        }
        catch (IOException e)
        {
            String msg = e.getMessage();
            IJ.showMessage(plugin_name, msg.equals("") ? "" + e : msg);
            return;
        }
    }

    private ImageStack createStack(InputStream is) throws IOException
    {
        int     error_code;

        // Extract informations from Header
        IJ.showStatus("Parsing header...");
        parse_header(is);

        nb_frame_pixel = width * height;
        frame_size = nb_frame_pixel * (bit_depth / 8);

        // Check the extracted innformations from header
        IJ.showStatus("Checking data integrity...");
        if ((error_code = check_data_integrity()) != 0)
        {
            display_message(error_code);
            return null;
        }

        IJ.showStatus("Reading images...");
        return parse_image(is);
    }

    private int check_data_integrity()
    {
        if (magic_number != 1330401096) // 1330401096 == "HOLO"
            return 1;
        if (version != 2 && version != 1 && version != 0) // TODO: Manage other version of holo files
            return 2;
        if (bit_depth != 8 && bit_depth != 16)
            return 3;
        if (data_size != (long)frame_size * num_frames)
            return 4;
        if (endianness != 0 && endianness != 1)
            return 5;
        return 0;
    }

	private void parse_header(InputStream is) throws IOException
    {
        try
        {
            byte[]  buf   = new byte[max_header_size];
            short[] u_hdr = new short[max_header_size];
            int     i;
            int     read_bytes = 0;

            // Get magic number and version
            read_bytes = is.read(buf, 0, 6);
            if (read_bytes != 6)
                throw new IOException("Error reading file (header)");

            // Converting values to unsigned
            for (i = 0; i < 6; ++i)
                u_hdr[i] = (short)(buf[i] & 0xFF);

            magic_number = u_hdr[0] | (u_hdr[1] << 8) | (u_hdr[2] << 16) | (u_hdr[3] << 24);
            version      = u_hdr[4] | (u_hdr[5] << 8);

            // Reading last bytes from header
            if (version == 2 || version == 1)
            {
                read_bytes = is.read(buf, 6, 58); // 58 + 6 = 64 total header bytes
                if (read_bytes != 58)
                    throw new IOException("Error reading file (header)");
            }
            else if (version == 0)
            {
                read_bytes = is.read(buf, 6, 12); // 12 + 6 = 18 total header bytes
                if (read_bytes != 12)
                    throw new IOException("Error reading file (header)");
            }

            // Converting values to unsigned
            for (i = 0; i < max_header_size; ++i)
                u_hdr[i] = (short)(buf[i] & 0xFF);

            // Extracting values
            bit_depth  = u_hdr[ 6] | (u_hdr[ 7] << 8);
            width      = u_hdr[ 8] | (u_hdr[ 9] << 8) | (u_hdr[10] << 16) | (u_hdr[11] << 24);
            height     = u_hdr[12] | (u_hdr[13] << 8) | (u_hdr[14] << 16) | (u_hdr[15] << 24);
            num_frames = u_hdr[16] | (u_hdr[17] << 8) | (u_hdr[18] << 16) | (u_hdr[19] << 24);

            // If version == 0
            data_size  = (long)width * height * num_frames * (bit_depth / 8);
            endianness = 0;

            if (version == 2 || version == 1)
            {
                data_size  = (u_hdr[20] <<  0) | (u_hdr[21] <<  8) | (u_hdr[22] << 16) | (u_hdr[23] << 24)
                           | (u_hdr[24] << 32) | (u_hdr[25] << 40) | (u_hdr[26] << 48) | (u_hdr[27] << 56);
                endianness = u_hdr[28];
            }

        }
        catch (IOException e)
        {
            String msg = e.getMessage();
            IJ.showMessage(plugin_name, msg.equals("") ? "" + e : msg);
        }
    }

    private ImageStack parse_image(InputStream is) throws IOException
    {
        try
        {
            ImageStack  stack = new ImageStack(width, height);
            byte[]      batch_slice = new byte[frame_size * batch_read];
            int         read_bytes;
            int         read_images;
            float       percent;

            for (int i = 0; i < num_frames; i += read_images)
            {
                // Status bar
                percent = (i / (float)num_frames) * 100;
                IJ.showStatus("Reading images... " + String.valueOf(i) + "/" + String.valueOf(num_frames) + " (" + String.format("%.2f", percent) + "%)");

                // Read "batch_read" frames
                read_bytes = is.read(batch_slice);
                read_images = read_bytes / frame_size;

                if (read_bytes != frame_size * batch_read && i + read_images < num_frames)
                    throw new IOException("Error reading file (frame " + String.valueOf(i) + "/" + String.valueOf(num_frames) + ")");

                for (int j = 0; j < read_images; ++j)
                {
                    byte[]  slice8 = new byte[frame_size];
                    short[] slice16 = new short[nb_frame_pixel];

                    // Convert the frame in the desired bit depth and append to the stack
                    if (bit_depth == 8)
                    {
                        System.arraycopy(batch_slice, j * frame_size, slice8, 0, frame_size);
                        stack.addSlice("", slice8);
                    }
                    if (bit_depth == 16)
                    {
                        if (endianness == 0)
                        {
                            for (int pixel = 0; pixel < nb_frame_pixel; ++pixel)
                                slice16[pixel] = (short)((batch_slice[(j * frame_size) + (pixel * 2 + 0)] & 0xFF) | ((batch_slice[(j * frame_size) + (pixel * 2 + 1)] & 0xFF) << 8));
                        }
                        else if (endianness == 1)
                        {
                            for (int pixel = 0; pixel < nb_frame_pixel; ++pixel)
                                slice16[pixel] = (short)((batch_slice[(j * frame_size) + (pixel * 2 + 1)] & 0xFF) | ((batch_slice[(j * frame_size) + (pixel * 2 + 0)] & 0xFF) << 8));
                        }
                        stack.addSlice("", slice16);
                    }
                }
            }
            return stack;
        }
        catch (IOException e)
        {
            String msg = e.getMessage();
            IJ.showMessage(plugin_name, msg.equals("") ? "" + e : msg);
        }
        return null;
    }

    private void display_message(int error_code)
    {
        if (error_code == 1)
            IJ.showMessage("ERROR: " + plugin_name, "Bad Magic Number: " + String.valueOf(magic_number));
        else if (error_code == 2)
            IJ.showMessage("ERROR: " + plugin_name, "Bad Version: " + String.valueOf(version));
        else if (error_code == 3)
            IJ.showMessage("ERROR: " + plugin_name, "Bad Bit Depth: " + String.valueOf(bit_depth));
        else if (error_code == 4)
            IJ.showMessage("ERROR: " + plugin_name, "Bad Data Size: " + String.valueOf(data_size));
        else if (error_code == 5)
            IJ.showMessage("ERROR: " + plugin_name, "Bad Endianness: " + String.valueOf(endianness));
    }
}
