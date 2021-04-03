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

    private int                 bit_depth;
    private int                 width;
    private int                 height;

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
        writeString("HOLO"); // Magic number

        raFile.seek(4);
        writeInt(2); // Version number

        bit_depth = imp.getBitDepth();
        raFile.seek(6);
        writeInt(bit_depth); // Number of bits per pixel

        width = imp.getWidth();
        raFile.seek(8);
        writeInt(width); // Width of the images

        height = imp.getHeight();
        raFile.seek(12);
        writeInt(height); // Height of the images

        int num_frames = imp.getStackSize();
        raFile.seek(16);
        writeInt(num_frames); // Number of images

        long data_size = (long)width * height * num_frames * (bit_depth / 8);
        raFile.seek(20);
        writeLong(data_size); // Total data size in bytes

        raFile.seek(28);
        writeInt(0); // Endianness : here 0 => little endian

        raFile.seek(29);
        byte[] padding = new byte[35];
        Arrays.fill(padding, (byte)0);
        raFile.write(padding); // Padding to make the header 64 bytes long

        raFile.seek(63);

        bufferWrite = new byte[(bit_depth/8) * width * height];

        for(int i = 0; i < num_frames; i++)
        {
            // Status bar
            IJ.showProgress((double)(i+1) / num_frames);

            raFile.seek(64 + height * width * (bit_depth / 8) * i);

            writeByteFrame(i+1);
        }
        raFile.close();
    }

    private void writeByteFrame(int slice) throws IOException
    {
        ImageProcessor ip = imp.getStack().getProcessor(slice);
        //ip = ip.convertToByte(true);

        if(bit_depth == 8)
        {
            byte[] pixels = (byte[])ip.getPixels();
            raFile.write(pixels);
        }

        if(bit_depth == 16)
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
}
