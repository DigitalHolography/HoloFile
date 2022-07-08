function Output = Read_Holo(input_file)

%  Opens .holo image sequences.
% 
%   A holo file contains a header, raw data and a footer.
%   The header speficy how raw data are formatted and the footer provide information about digital hologram rendering parameters.
% 
%   Find more at: https://ftp.espci.fr/incoming/Atlan/holovibes/holo/HoloFileSpecification.pdf
 
% Open .holo file 

%% Check if input_file is empty or not 
switch nargin 
    case 1 
        path_filename = input_file;              
    otherwise 
        [filename,path] = uigetfile('*.holo');

        if isequal(filename, 0)
            disp('User selected Cancel');
            return;
        else
            disp(['User selected ', fullfile(path, filename)]);
        end

        path_filename = fullfile(path, filename);
end

wait = waitbar(0, 'Parse header...');
pause(.5);

%% Parse header 
header_mmap = memmapfile(path_filename, 'Format', ...
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

% magic_number = header_mmap.Data.magic_number;     % Magic number, always set to "HOLO"
% version = header_mmap.Data.version;               % Version of holo file
num_frames = header_mmap.Data.num_frames;           % Total number of frames in raw data
frame_width = header_mmap.Data.width;               % Width of a frame
frame_height = header_mmap.Data.height;             % Height of a frame
% data_size = header_mmap.Data.total_size;          % Total raw data size (always equals to width * height * num_frames * (bit_depth / 8))
bit_depth = header_mmap.Data.bit_depth;             % Bit depth of raw data
endianness = header_mmap.Data.endianness;           % Endianness of raw data

if endianness == 0
    endian = 'l'; % big endian
else
    endian = 'b'; % little endian 
end

if bit_depth == 8
    type = 'uint8';
elseif bit_depth == 16
    type = 'uint16';
end

waitbar(1/4, wait, 'Parse images...');
pause(.5);

%% Parse images
fd = fopen(path_filename, 'r');

header_size = (64); % the header is 64-bit longer 

frame_batch = zeros(frame_width, frame_height, num_frames, type);    

frame_size = uint64(frame_width * frame_height * uint32(bit_depth / 8));
 
fseek(fd, header_size, 'bof');

waitbar(2/4, wait, 'Parse images...');
pause(.5);

for i = 1:num_frames
    waitbar((2 + double(i / num_frames)) / 4, wait, 'Please wait...');

    fseek(fd, header_size + frame_size * uint64(i-1), 'bof');

    if bit_depth == 8
        frame_batch(:, :, i) = reshape(fread(fd, frame_width * frame_height, 'uint8=>uint8', endian), frame_width, frame_height);
    elseif bit_depth == 16
        frame_batch(:, :, i) = reshape(fread(fd, frame_width * frame_height, 'uint16=>uint16', endian), frame_width, frame_height);
    end  
end

fclose(fd);

waitbar(4/4, wait, 'Movie Player is opening...');

%% Play image sequences or fill the Output 
switch nargout 
    case 1 
        Output = frame_batch; 
    otherwise
        implay(rot90(flipud(frame_batch(:, :, :)),3), 30); %30 fps arbitrary value      
end

close(wait);
end