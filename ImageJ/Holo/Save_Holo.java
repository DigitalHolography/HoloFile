import ij.*;
import ij.process.*;
import ij.io.*;
import ij.plugin.*;
import java.io.*;
import java.nio.*;
import java.util.*;

/**
 *  Write .holo image sequences.
 *
 *  A holo file contains a header, raw data and a footer.
 *  The header speficy how raw data are formatted and the footer provide information about digital hologram rendering parameters.
 *
 *  Find more at: https://ftp.espci.fr/incoming/Atlan/holovibes/holo/HoloFileSpecification.pdf
 */

public class Save_Holo implements PlugIn
{
    private ImagePlus           imp;
    private RandomAccessFile    raFile;

    private String              plugin_name = "Save_Holo";
    private int                 frame_size;         // Size in bytes of a frame (equals to: width * height * bit_depth)

    // Header variables
    private String              magic_number;       // Magic number, always set to "HOLO"
    private int                 version;            // Version of holo file
    private int                 bit_depth;          // Bit depth of raw data
    private int                 width;              // Width of a frame
    private int                 height;             // Height of a frame
    private int                 num_frames;         // Total number of frames in raw data
    private long                data_size;          // Total raw data size (always equals to width * height * num_frames * (bit_depth / 8))
    private int                 endianness;         // Endianness of raw data
    private byte[]              padding;            // Padding to make the header 64 bytes long

    private byte[]              bufferWrite;
    private File                file;

    public void run(String arg)
    {
        try
        {
            imp = WindowManager.getCurrentImage();
            if (imp == null)
            {
                IJ.showMessage("INFO: " + plugin_name, "To save as holo, first open an image.");
                return ;
            }
            writeImage(imp);
        }
        catch(IOException e)
        {
            IJ.showMessage("Write Holo", "An error occured writing the file.\n \n" + e);
        }
        IJ.showStatus("");
    }

    private void writeImage(ImagePlus imp) throws IOException
    {
        int   error_code;
        float progress;

        // Open dialog to save a file in .holo
        SaveDialog sd = new SaveDialog("Save as HOLO...", imp.getTitle(), ".holo");

        String fileName = sd.getFileName();
        String fileDir = sd.getDirectory();

        if (fileName == null || fileDir == null)
            return;


        // Get header informations from current images stacks
        magic_number = "HOLO";
        version = 2;
        bit_depth = imp.getBitDepth();
        width = imp.getWidth();
        height = imp.getHeight();
        num_frames = imp.getStackSize();
        data_size = (long)width * height * num_frames * (bit_depth / 8);
        endianness = 0;

        frame_size = width * height * (bit_depth / 8);

        // Check the extracted informations
        IJ.showStatus("Checking data integrity...");
        if ((error_code = check_data_integrity()) != 0)
        {
            display_message(error_code);
            return;
        }

        IJ.showStatus("Writing header...");
        file = new File(fileDir + fileName);
        file.delete();
        raFile = new RandomAccessFile(file, "rw");

        // Writing 64-byte binary header
        raFile.seek(0);
        writeString(magic_number);

        raFile.seek(4);
        writeInt(version);

        raFile.seek(6);
        writeInt(bit_depth);

        raFile.seek(8);
        writeInt(width);

        raFile.seek(12);
        writeInt(height);

        raFile.seek(16);
        writeInt(num_frames);

        raFile.seek(20);
        writeLong(data_size);

        raFile.seek(28);
        writeInt(endianness);

        raFile.seek(29);
        padding = new byte[35];
        Arrays.fill(padding, (byte)0);
        raFile.write(padding);

        raFile.seek(63);

        bufferWrite = new byte[frame_size];

        for(int i = 0; i < num_frames; i++)
        {
            // Status and Progress Bar
            progress = (i + 1) / (float)num_frames;
            IJ.showStatus("Writing images... " + String.valueOf(i + 1) + "/" + String.valueOf(num_frames)
                                               + " (" + String.format("%.2f", progress * 100) + "%)");
            IJ.showProgress(progress);

            raFile.seek(64 + (long)frame_size * i);
            writeByteFrame(i + 1); // Slice index begins at 1
        }
        raFile.close();
    }

    private void writeByteFrame(int slice) throws IOException
    {
        ImageProcessor ip = imp.getStack().getProcessor(slice);

        if (bit_depth == 8)
        {
            byte[] pixels = (byte[])ip.getPixels();
            raFile.write(pixels);
        }

        else if (bit_depth == 16)
        {
            short[] pixels = (short[])ip.getPixels();

            for (int i = 0; i < width * height; ++i)
            {
                bufferWrite[i * 2 + 1]  = (byte)(pixels[i] >> 8);
                bufferWrite[i * 2]      = (byte)(pixels[i] & 0xFF);
            }
            raFile.write(bufferWrite);
        }
    }

    private void writeString(String s) throws IOException
    {
        raFile.write(s.getBytes());
    }

    private void writeInt(int v) throws IOException
    {
        raFile.write((byte)(v & 0xFF));
        raFile.write((byte)((v >>  8) & 0xFF));
        raFile.write((byte)((v >> 16) & 0xFF));
        raFile.write((byte)((v >> 24) & 0xFF));
    }

    private void writeLong(long v) throws IOException
    {
        raFile.write((byte)(v & 0xFF));
        raFile.write((byte)((v >>  8) & 0xFF));
        raFile.write((byte)((v >> 16) & 0xFF));
        raFile.write((byte)((v >> 24) & 0xFF));
        raFile.write((byte)((v >> 32) & 0xFF));
        raFile.write((byte)((v >> 40) & 0xFF));
        raFile.write((byte)((v >> 48) & 0xFF));
        raFile.write((byte)((v >> 56) & 0xFF));
    }

    private int check_data_integrity()
    {
        if (bit_depth != 8 && bit_depth != 16)
            return 1;
        return 0;
    }

    private void display_message(int error_code)
    {
        if (error_code == 1)
        {
            IJ.showMessage("ERROR: " + plugin_name, "Bit depth not supported: " + String.valueOf(bit_depth));
            IJ.showMessage("Please edit the image type");
        }
    }
}
