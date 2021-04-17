function Write_Holo(input_array, filepath)

%  Write .holo image sequences.
% 
%   A holo file contains a header, raw data and a footer.
%   The header speficy how raw data are formatted and the footer provide information about digital hologram rendering parameters.
% 
%   Find more at: https://ftp.espci.fr/incoming/Atlan/holovibes/holo/HoloFileSpecification.pdf

%% Check if filepath is empty or not 
switch nargin 
     case 1 
        [filename, path] = uiputfile('*.holo');

        if isequal(filename, 0)
            disp('User selected Cancel');
        else
            disp(['User selected ', fullfile(path, filename)]);
        end
        path_filename = fullfile(path, filename);
    otherwise 
        path_filename = [filepath, '.holo']; 
end

%% Parse input_array
batch = whos('input_array');

%%Check the array size 
if numel(size(input_array)) < 2 && numel(size(input_array)) > 3 
   error('The array must be in 2D or 3D');  
end

frames_size = batch.size;
data_size = batch.bytes;

frame_width = frames_size(1);
frame_height = frames_size(2);
num_frames =  frames_size(3);

bit_depth = 8 * ceil(data_size / (frame_width * frame_height * num_frames)); % in bits 

%%Check the bit depth 
if not(bit_depth == 8) && not(bit_depth == 16)
    error('Bit depth not supported, please edit the type');
end

if bit_depth == 8 
    type = 'uint8';
elseif bit_depth == 16
    type = 'uint16';
end

%% Open & write a new .holo file
fd = fopen(path_filename, 'w');

%%Write the header 
fwrite(fd, 'HOLO');                         % Magic number, always set to "HOLO"
fwrite(fd, 2, 'uint16');                    % Version of holo file
fwrite(fd, bit_depth, 'uint16');            % Bit depth of data
fwrite(fd, frame_width, 'uint32');          % Width of a frame
fwrite(fd, frame_height, 'uint32');         % Height of a frame
fwrite(fd, num_frames, 'uint32');           % Total number of frames in data
fwrite(fd, data_size, 'uint64');            % Total data size (always equals to width * height * num_frames * (bit_depth / 8))
fwrite(fd, 0, 'uint8');                     % Endianness, here 0 => little endian 
fwrite(fd, zeros(1, 35), 'uint8');          % Padding to make the header 64 bytes long

%%Write the data 
fwrite(fd, input_array, type);

fclose(fd);

end