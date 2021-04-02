import ij.*;
import ij.plugin.PlugIn;
import ij.process.*;
import ij.gui.*;
import ij.io.*;
import ij.plugin.Animator;
import java.awt.*;
import java.awt.image.*;
import java.io.*;
import java.util.*;
import ij.plugin.*;

public class Write_Holo_test implements PlugIn
{
    private ImagePlus imp;
    private RandomAccessFile raFile;
    private int bit_depth;

    private byte[] bufferWrite;
    private File file;

    public void run(String arg) //String arg
    {
        //ImageWindow iw;

        try
        {
            // iw = WindowManager.getCurrentImage();
            // imp = iw.getImagePlus();
            imp = WindowManager.getCurrentImage();
            writeImage(imp);
            IJ.showStatus("");
        }catch(IOException e) {
            IJ.showMessage("Write Holo", "An error occured writing the file.\n \n" + e);
        }
        IJ.showStatus("");
    }

    public void writeImage(ImagePlus imp) throws IOException
    {
        long saveFileSize;
        long[] saved_lenght;

        SaveDialog sd = new SaveDialog("Save as HOLO...", imp.getTitle(), ".holo");
        String fileName = sd.getFileName();
        if (fileName == null)
            return;
        String fileDir = sd.getDirectory();
        file = new File(fileDir + fileName);
        raFile = new RandomAccessFile(file, "rw");

        raFile.seek(0);
        writeString("HOLO"); //magic number
        //saveFileSize = raFile.getFilePointer();
        raFile.seek(4);
        writeInt(2); //version
        bit_depth = imp.getBitDepth();
        //IJ.showMessage("bit_depth" + String.valueOf(bit_depth));
        int width = imp.getWidth();
        //IJ.showMessage("width" + String.valueOf(width));
        int height = imp.getHeight();
        //IJ.showMessage("height" + String.valueOf(height));
        int num_frames = imp.getStackSize();
        //IJ.showMessage("num_frames" + String.valueOf(num_frames));
        long data_size = (long)width * height * num_frames * (bit_depth / 8);
        //IJ.showMessage("data_size" + String.valueOf(data_size));
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
        writeInt(0); // endianness : here 0 => little endian
        raFile.seek(29);

        byte[] padding = new byte[35];
        Array.fill(padding, 0);
        writeInt(padding); // padding

        raFile.seek(63);

        //int stack = imp.getStackSize();
        //saved_lenght = new long[num_frames];

        bufferWrite = new byte[(bit_depth/8) * width * height];

        for(int i = 0; i < num_frames; i++)
        {
            IJ.showProgress((double)i / num_frames);
            //saved_lenght[i] = raFile.getFilePointer();
            raFile.seek(64 + height * width * (bit_depth/8) * i);
            //writeInt(bit_depth * width * height);
            writeByteFrame(i+1);
        }
        raFile.close();
    }

    private void writeByteFrame(int slice) throws IOException
    {
        ImageProcessor ip = imp.getStack().getProcessor(slice);
        //ip = ip.convertToByte(true);
        short[] pixels = (short[])ip.getPixels();
        int width = imp.getWidth();
        int height = imp.getHeight();
        // int offset, index = 0;
        // for (int y = height - 1; y >= 0; y--)
        // {
        //     offset = y * width;
        //     for(int x = 0; x < width; x++)
        //     {
        //         bufferWrite[index] = pixels[index];
        //         index++;
        //     }
        // // }
        // System.arraycopy(pixels, 0, bufferWrite, 0, width * height * (bit_depth / 8));
        for (int i = 0; i < width * height; ++i)
        {
            bufferWrite[i * 2 + 1] = (byte)(pixels[i] >> 8);
            bufferWrite[i * 2] = (byte)(pixels[i] & 0xFF);
        }

        raFile.write(bufferWrite);
    }

     final void writeString(String s) throws IOException
    {
        raFile.write(s.getBytes());
    }

    final void writeInt(int v) throws IOException
    {
        raFile.write((byte)(v & 0xFF));
        raFile.write((byte)((v >>  8) & 0xFF));
        raFile.write((byte)((v >> 16) & 0xFF));
        raFile.write((byte)((v >> 24) & 0xFF));
    }

    final void writeLong(long v) throws IOException
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
}
