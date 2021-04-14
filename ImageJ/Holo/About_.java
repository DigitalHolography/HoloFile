import ij.*;
import ij.plugin.*;

/**
 *  This the section About of the Holo plugin set.
 * 
 *  Find more at: https://ftp.espci.fr/incoming/Atlan/holovibes/holo/HoloFileSpecification.pdf
 */

public class About_ implements PlugIn
{
    private String version = "1.0.0";
    private String holo_file_specification_link = "https://ftp.espci.fr/incoming/Atlan/holovibes/holo/HoloFileSpecification.pdf";
    
    public void run(String arg)
    {
        IJ.showMessage("About", "<html>"
        + "<center><h2>Holo Plugins (v" + version + ")</h2></center>"
        + "<br/>"
        + "<center>This set of plugins aims to facilitate the opening and saving of holo files.</center>"
        + "<br/>"
        + "<center>Find more at: " + "<a href=" + holo_file_specification_link + ">HoloFileSpecification</a></center>");
    }
}