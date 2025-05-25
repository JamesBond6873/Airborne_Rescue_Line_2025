function ViewColorSpaces
rgbim = imread('test_moments\silver_line.jpg');
ViewColorSpaces2(rgbim)


function ViewColorSpaces2(rgb_image)
% ViewColorSpaces(rgb_image)
% displays an RGB image in 4 different color spaces. RGB, HSV, YCbCr,CIELab
% each of the 3 channels are shown for each colorspace
% the display mimcs the  New matlab color thresholder window
% http://www.mathworks.com/help/images/image-segmentation-using-the-color-thesholder-app.html

hsvim = rgb2hsv(rgb_image);
yuvim = rgb2ycbcr(rgb_image);

%cielab colorspace
cform = makecform('srgb2lab');
cieim = applycform(rgb_image,cform);

h= figure();
%rgb
subplot(3,4,1);imshow(rgb_image(:,:,1));title(sprintf('RGB Space\n\nred'))
subplot(3,4,5);imshow(rgb_image(:,:,2));title('green')
subplot(3,4,9);imshow(rgb_image(:,:,3));title('blue')

%hsv
subplot(3,4,2);imshow(hsvim(:,:,1));title(sprintf('HSV Space\n\nhue'))
subplot(3,4,6);imshow(hsvim(:,:,2));title('saturation')
subplot(3,4,10);imshow(hsvim(:,:,3));title('brightness')
figure; mesh(hsvim(:,:,3))
figure(h)

%ycbcr / yuv
subplot(3,4,3);imshow(yuvim(:,:,1));title(sprintf('YCbCr Space\n\nLuminance'))
subplot(3,4,7);imshow(yuvim(:,:,2));title('blue difference')
subplot(3,4,11);imshow(yuvim(:,:,3));title('red difference')

%CIElab
subplot(3,4,4);imshow(cieim(:,:,1));title(sprintf('CIELab Space\n\nLightness'))
subplot(3,4,8);imshow(cieim(:,:,2));title('green red')
subplot(3,4,12);imshow(cieim(:,:,3));title('yellow blue')



