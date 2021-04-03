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

public class Write_Holo implements PlugIn
{
    private ImagePlus           imp;
    private RandomAccessFile    raFile;

    private String              plugin_name = "Write Holo";

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
            writeImage(imp);
            IJ.showStatus("");
        }
        catch(IOException e)
        {
            IJ.showMessage("Write Holo", "An error occured writing the file.\n \n" + e);
        }
        IJ.showStatus("");
    }

    private void writeImage(ImagePlus imp) throws IOException
    {
        int error_code;

        // Open dialog to save a file in .holo
        SaveDialog sd = new SaveDialog("Save as HOLO...", imp.getTitle(), ".holo");

        String fileName = sd.getFileName();
        if (fileName == null)
            return;

        String fileDir = sd.getDirectory();

        file = new File(fileDir + fileName);
        raFile = new RandomAccessFile(file, "rw");

        // Writing 64-byte binary header
        raFile.seek(0);
        magic_number = "HOLO";
        writeString(magic_number);

        raFile.seek(4);
        version = 2;
        writeInt(version);

        raFile.seek(6);
        bit_depth = imp.getBitDepth();
        writeInt(bit_depth);

        raFile.seek(8);
        width = imp.getWidth();
        writeInt(width);

        raFile.seek(12);
        height = imp.getHeight();
        writeInt(height);

        raFile.seek(16);
        num_frames = imp.getStackSize();
        writeInt(num_frames);

        raFile.seek(20);
        data_size = (long)width * height * num_frames * (bit_depth / 8);
        writeLong(data_size);

        raFile.seek(28);
        endianness = 0;
        writeInt(endianness);

        raFile.seek(29);
        padding = new byte[35];
        Arrays.fill(padding, (byte)0);
        raFile.write(padding);

        // Check the extracted informations
        IJ.showStatus("Checking data integrity...");
        if ((error_code = check_data_integrity()) != 0)
        {
            display_message(error_code);
        }

        raFile.seek(63);

        bufferWrite = new byte[(bit_depth / 8) * width * height];

        for(int i = 0; i < num_frames; i++)
        {
            // Status bar
            IJ.showProgress((double)(i + 1) / num_frames);

            raFile.seek(64 + height * width * (bit_depth / 8) * i);
            writeByteFrame(i + 1);
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

    final void writeString(String s) throws IOException
    {
        raFile.write(s.getBytes());
    }

    final void writeInt(int v) throws IOException
    {
        raFile.write((byte) (v & 0xFF));
        raFile.write((byte) ((v >>  8) & 0xFF));
        raFile.write((byte) ((v >> 16) & 0xFF));
        raFile.write((byte) ((v >> 24) & 0xFF));
    }

    final void writeLong(long v) throws IOException
    {
        raFile.write((byte) (v & 0xFF));
        raFile.write((byte) ((v >>  8) & 0xFF));
        raFile.write((byte) ((v >> 16) & 0xFF));
        raFile.write((byte) ((v >> 24) & 0xFF));
        raFile.write((byte) ((v >> 32) & 0xFF));
        raFile.write((byte) ((v >> 40) & 0xFF));
        raFile.write((byte) ((v >> 48) & 0xFF));
        raFile.write((byte) ((v >> 56) & 0xFF));
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
            IJ.showMessage("ERROR: " + plugin_name, "Not supporting bit Depth: " + String.valueOf(bit_depth));
            IJ.showMessage("Please edit the image type");
        }
    }


}
