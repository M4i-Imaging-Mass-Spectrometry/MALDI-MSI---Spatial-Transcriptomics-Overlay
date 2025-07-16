README

### EscDat-Trans ###

#Walk through/work flow

"Software GUI buttons"

-	Once a subprogram is started, the buttons on the main EscDatTrans interface will become unresponsive and the button of the running subprogram colors red. After successful completion of the subprogram, all buttons become responsive again and the finished subprogram button colors green. 
-	If the main interface "freezes" because of an unforeseen error, the analysis can be continued by enabling all buttons again by clicking the "Unlock" button in the right lower corner.

START
"Choose Data"
-	Start new analysis: Select the Bruker timsTOF.d base folder
or 
-	select an existing EscDat analysis folder: Select folder from existing 'analysis.d/EscDat' folder (select folder on date EscDat analysis)


"Choose Optical Image"
-	Select the (ome.)tiff optical (fluorescence) file (often found in "xenium output folder\morphology_focus\morphology_focus_0000.ome.tif")

-	Select a resolution from "Resolutions in OME.TIF file" window, ideally a resolution matching your MSI image resolution and click 'OK'.


"1. Create LowRes dataset"
-	Start creation of full spatial resolution, low mass resolution datafile for use in step "2 data Explorer"


"2. Data Explorer"
-	Check 'Normalize' box if needed, normalization of the MSI data (spectral wise, the summed intensities per spectrum is constant) can give a better contrast in the image.

-	Select m/z channel for representative image display by left mouseclick on a peak in the mass spectrum or input a m/z channel by hand in the M/Z field and press 'Plot' button. 

You can move through m/z channels with 'previous'/'next' buttons
'TIC' button to display TIC image
You can change colour maps by right clicking on the scalebar and select 'standard colormaps', choose your prefered colormap.
 
'Save image for EscDat Coregistration' will save the image in the analysis folder.

-	To enhance contrast summation, a combination of m/z channels can be compiled by sequential selection of m/z channels followed by clicking 'Numerator' button for the first m/z channel and the '+' button for consecutive m/z channels. Using the 'Numerator' button again will reset the stored sequence.

-	Adding m/z channels using the 'Denominator' button is also possible, '1' resets.
Once the Numerator (and Denominator if needed) m/z channels are choosen, the 'Plot Ratio' button shows the resulting image.

-	Click 'Save image for EscDat Coregistration' will save the image in the analysis folder.

-	Closing the window automatically saves your selection.


"3. Coregistration"
-	Click 'Select Mass Image' to select the MSI image created in the previous step 'Data Explorer' (this file starts with 'Image_').

-	Click 'Select ROI' and create a ROI on the image by clicking and dragging. Since the MSI image is most likely fully covered by the optical image, selecting the full image by dragging the anchor points to the edges on the ROI (blue lines) is advised.

-	Double click in the ROI selection to save and close.

-	Repeat 'Select ROI' in the Optical Image frame, select the appropriate ROI.

-	Click 'HR Control Point Selection'

-	Choose a grid cell in Microscope Image frame by clicking on it.

-	Choose corresponding grid cell in MS Image frame.

-	To be able to see the marks left by the MALDI laser ablation, the 'Upper Threshold' value has to be lowered to about 0.004, lower the value and click 'Refresh'.

-	Click the + icon on the right top of the big black and white microscope Image to enable zooming.

-	Zoom in Microscope Image to find fiducial marker points in laser ablation.

-	Zoom in to MS Image to find corresponding MSI spectrum.

-	Click 'Select point' under Microscope Image, input number of point to add and click on the marker point to store it.

-	Click 'Select point' under MS Image, input number of point to add (same as corresponding Microscope Image point) and click on the marker point to store it.

-	Repeat for all registration points. ( choose minimum of 4 registration points)

-	The background image in the MS Image can be set to a specific m/z channel if needed by clicking on the appropriate m/z channel in the spectrum on the lower right.

-	An individual MS spectrum can be viewed for inspection by clicking on the 'Spectrum' button and clicking on a spectrum position in the MS Image.

-	To select the next block in the grid on the left first deactivate zoom or panning in the top right popup in any of the images.

-	Repeat above procedure until all registration points are set.

-	Close registration tool

-	In the 'Registration' frame select the desired transformation type.

-	Click 'Coregister' button

The Registration Result Overlay will be drawn on the screen, select a grid cell to display in detail, turn zoom on and off by toggling the 'Zoom on' tick box.

If the result of the registration is as desired close the ECoRegT interface, if not: add or replace registration points by clicking 'HR Control Point Selection' again.

If you want to continue from a previous overlay, press "Load and adapt previous registration points".


"4 10X Xenium Explorer ROI selection"
-	In this step, you need to run  a different python script separately. Please check "https://github.com/M4i-Imaging-Mass-Spectrometry/MALDI-MSI---Spatial-Transcriptomics-Overlay" for the aforementioned python script.
The script creates a .geojson file containing "cell_id, cluster, gene transcript and spatial coordinates" which can be read in step number 5. 


"5 Create HR ROI dataset"
-	This software overlays the cell coordinates (detected in the Xenium Explorer software and exported using the provided Python script) with the MSI data and extracts the high resolution mass spectrum for each cell. MSI spectra are weighed by the amount of overlap. The cell cluster as assigned in the Xenium Explorer software is also stored.

The default settings should suffice:
Number of closest pixels: Maximum number of pixels to take into account per cell
Minimal coverage per MSI pixel(%): Only include spectra from pixels that have a minimal overlap of the given percentage. A value of 100% will only include pixels that are fully covered by the cell circumference.
GeoJSON um per pixel: The GeoJSON data is represented in um, this has to be expressed in pixels. Optical resolution of the Optical image (um per pixel), in our case always 0.2125 um/pixel (This is based on the optical resolution on the Xenium Microscope). 
% data to use for peakpicking: Once the extraction of the spectra starts, a full resolution mass spectrum is created that is used for the extraction of peak apex and peak windows. The resulting peaklist is used to extract the high mass resolution spectra for all cells.
To increase the speed of the process one may choose to only use a percentage of the full dataset to create the full resolution mass spectrum.

-	Click the 'Peakpick combined ROIS and Create EscDatResult.csv file'
PEAPI Peackpicking interface will be shown

- 	Click 'Pick!' button
The detected peaks will be displayed, zoom in to check quality. The top graph shows the peak apex (blue dotted line) and integration window (small black lines), the lower graph the integration result. The number of peaks can be limited by increasing the 'Threshold' value.
Peak detection in the high m/z region can be enhanced by changing the 'Boost high masses' value, a number >1 will linearly multiply the m/z intensities by 1 for the first m/z channel to 'number' by the last m/z channel. e1,e2 will multiply by e^1,e^2 etc.

-	Once satisfied with the result, click 'Save and Continue' to start data extraction.

STOP

RESULTING OUTPUT:
EscDatResult_Cell_With_Nucleus_30_0_10-Jul-2025_15-09-14.csv" (for general statistical analysis) NOTE: GF (Gene Features) are ranked in the final .csv files in alphabetical order.
EscDatResult_Seurat_Cell_With_Nucleus_30_0_10-Jul-2025_15-09-14.csv" (for Seurat based statistical analysis)
EscDatResult_summary_Cell_With_Nucleus_30_0_10-Jul-2025_15-09-14.csv" (generic summary file)
ROIspectra_Cell_With_Nucleus_30_0_10-Jul-2025_15-09-14.mat" (for Matlab based analysis)





 
