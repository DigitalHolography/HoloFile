function Write_Holo()

%  Write .holo image sequences.
% 
%   A holo file contains a header, raw data and a footer.
%   The header speficy how raw data are formatted and the footer provide information about digital hologram rendering parameters.
% 
%   Find more at: https://ftp.espci.fr/incoming/Atlan/holovibes/holo/HoloFileSpecification.pdf
 
%% Open file 
[filename,path] = uigetfile('*');

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
    endian = 'l'; % big endian
else
    endian = 'b'; % little endian 
end

if bit_depth == 8
    type = 'uint8';
else
    type = 'uint16';
end

%% Parse images
fd = fopen(fullfile(path, filename), 'r');

offset = 64; % the header is 64-bit longer 

frame_batch = zeros(frame_width, frame_height, num_frames, type);  
%frame_batch_16bit = zeros(frame_width, frame_height, num_frames, 'uint16');  

frame_size = frame_width * frame_height * uint32(bit_depth / 8);

width_range = 1:frame_width;
height_range = 1:frame_height; 

fseek(fd, offset, 'bof');

%wait = waitbar(0, 'Please wait...');

for i = 1:num_frames
    %waitbar(i / num_frames, wait);
    
    fseek(fd, offset + frame_size * (i-1), 'bof'); 
    
    if bit_depth == 8
        frame_batch(width_range, height_range, i) = reshape(fread(fd, frame_width * frame_height, 'uint8=>uint8', endian), frame_width, frame_height);
        
    elseif bit_depth == 16
        frame_batch(width_range, height_range, i) = reshape(fread(fd, frame_width * frame_height, 'uint16=>uint16', endian), frame_width, frame_height);
    end  
    
end

fclose(fd);

%% Write header 
batch = whos('frame_batch');

%%Check the matrix size 
if numel(size(frame_batch)) < 2
   error('The batch must be a 2D or 3D matrix');  
end

frames_size = batch.size;
data_size = batch.bytes;

frame_width = frames_size(1);
frame_height = frames_size(2);
num_frames =  frames_size(3);

bit_depth = 8 * ceil(data_size / (frame_width * frame_height * num_frames)); % in bits 

if bit_depth == 8 
    type = 'uint8';
elseif bit_depth == 16
    type = 'uint16';
end

%% Open & write a new .holo file
[filename, path] = uiputfile('*.holo');

if isequal(filename, 0)
    disp('User selected Cancel');
else
    disp(['User selected ', fullfile(path, filename)]);
end

fd = fopen(fullfile(path, filename), 'w');

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

%Write the data 
fwrite(fd, frame_batch, type);

fclose(fd);

end
