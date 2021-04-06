function Read_Holo()

%  Opens .holo image sequences.
% 
%   A holo file contains a header, raw data and a footer.
%   The header speficy how raw data are formatted and the footer provide information about digital hologram rendering parameters.
% 
%   Find more at: https://ftp.espci.fr/incoming/Atlan/holovibes/holo/HoloFileSpecification.pdf
 
%% Open .holo file 
[filename,path] = uigetfile('*.holo');

if isequal(filename,0)
    disp('User selected Cancel');
else
    disp(['User selected ', fullfile(path, filename)]);
end

 %% Parse header 
header_mmap = memmapfile(fullfile(path, filename), 'Format', ...
            {'uint8',   4,  'magic_number';...
             'uint16',  1,  'version';...
             'uint16',  1,  'bit_depth';...
             'uint32',  1,  'width';...
             'uint32',  1,  'height';...
             'uint32',  1,  'num_frames';...
             'uint64',  1,  'total_size';...
             'uint8',    1,  'endianness';...
             % padding - skip
            }, 'Repeat', 1);
   
if ~isequal(header_mmap.Data.magic_number', unicode2native('HOLO'))
    error('Bad holo file.');
end

%magic_number = header_mmap.Data.magic_number;      % Magic number, always set to "HOLO"
%version = header_mmap.Data.version;                % Version of holo file
num_frames = header_mmap.Data.num_frames;           % Total number of frames in raw data
frame_width = header_mmap.Data.width;               % Width of a frame
frame_height = header_mmap.Data.height;             % Width of a frame
%data_size = header_mmap.Data.total_size;           % Total raw data size (always equals to width * height * num_frames * (bit_depth / 8))
bit_depth = header_mmap.Data.bit_depth;             % Bit depth of raw data
endianness = header_mmap.Data.endianness;           % Endianness of raw data

if endianness == 0
    endian = 'b'; % big endian
else
    endian = 'l'; % little endian 
end

%% Parse images
fd = fopen(fullfile(path, filename), 'r');

offset = 65; % the header is 64-bit longer 

frame_batch_8bit = zeros(frame_width, frame_height, num_frames, 'uint8');  
frame_batch_16bit = zeros(frame_width, frame_height, num_frames, 'uint16');  

frame_size = frame_width * frame_height * uint32(bit_depth / 8);

width_range = 1:frame_width;
height_range = 1:frame_height; 

fseek(fd, offset, 'bof');

wait = waitbar(0, 'Please wait...');

for i = 1:num_frames
    waitbar(i / num_frames, wait);
    
    fseek(fd, offset + frame_size * (i-1), 'bof'); 
    
    if bit_depth == 8
        frame_batch_8bit(width_range, height_range, i) = reshape(fread(fd, frame_width * frame_height, 'uint8=>uint8', endian), frame_width, frame_height);
    elseif bit_depth == 16
        frame_batch_16bit(width_range, height_range, i) = reshape(fread(fd, frame_width * frame_height, 'uint16=>uint16', endian), frame_width, frame_height);
    end 
    
end

close(wait);

fclose(fd);

%% Play image sequences
if bit_depth == 8
    implay(rot90(flipud(frame_batch_8bit(:, :, :)),3), 30); %30 fps
elseif bit_depth == 16
    implay(rot90(flipud(frame_batch_16bit(:, :, :)),3), 30); %30 fps 
end

end
