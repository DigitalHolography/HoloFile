function Read_Holo()

[filename,path] = uigetfile('*.holo');

if isequal(filename,0)
    disp('User selected Cancel');
else
    disp(['User selected ', fullfile(path, filename)]);

header_mmap = memmapfile( fullfile(path, filename), 'Format',...
            {'uint8', 4, 'magic_number';...
             'uint16', 1, 'version';...
             'uint16', 1, 'bit_depth';...
             'uint32', 1, 'width';...
             'uint32', 1, 'height';...
             'uint32', 1, 'num_frames';...
             'uint64', 1, 'total_size';...
             'uint8', 1,  'endianness';...
             % padding - skip
            }, 'Repeat', 1);
   
if ~isequal(header_mmap.Data.magic_number', unicode2native('HOLO'))
    error('Bad holo file.');
end

%version = header_mmap.Data.version;
num_frames = header_mmap.Data.num_frames;
frame_width = header_mmap.Data.width;
frame_height = header_mmap.Data.height;
%data_size = header_mmap.Data.total_size;
bit_depth = header_mmap.Data.bit_depth;
endianness = header_mmap.Data.endianness;

if endianness == 0
    endian= 'b';
else
    endian= 'l';
end

fd = fopen( fullfile(path, filename), 'r');

offset = 65;

frame_batch_8bit = zeros(frame_width, frame_height, num_frames, 'uint8');  
frame_batch_16bit = zeros(frame_width, frame_height, num_frames, 'uint16');  

frame_size = frame_width * frame_height * uint32(bit_depth / 8);

width_range = 1:frame_width;
height_range = 1:frame_height; 

fseek(fd, offset, 'bof');

for i = 1:num_frames
    fseek(fd, offset + frame_size * (i-1), 'bof'); 
    
    if bit_depth == 8
        frame_batch_8bit(width_range, height_range, i) = reshape(fread(fd, frame_width * frame_height, 'uint8=>uint8', endian), frame_width, frame_height);
    elseif bit_depth == 16
        frame_batch_16bit(width_range, height_range, i) = reshape(fread(fd, frame_width * frame_height, 'uint16=>uint16', endian), frame_width, frame_height);
    end 
   
end

if bit_depth == 8
    implay(frame_batch_8bit(:,:,:),30); %30 fps
elseif bit_depth == 16
    implay(frame_batch_16bit(:,:,:),30); %30 fps
end

fclose(fd);

end


