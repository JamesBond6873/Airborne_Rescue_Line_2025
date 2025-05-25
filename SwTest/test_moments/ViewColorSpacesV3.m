function ViewColorSpacesV3
rgbim = imread('test_moments\latest_frame_original_Intersection_2.jpg');
ViewColorSpaces2(rgbim);
CalculateHSVThreshold(rgbim);


function ViewColorSpaces2(rgb_image)
hsvim = rgb2hsv(rgb_image);
yuvim = rgb2ycbcr(rgb_image);

% CIELab colorspace
cform = makecform('srgb2lab');
cieim = applycform(rgb_image,cform);

figure();
% RGB
subplot(3,4,1);imshow(rgb_image(:,:,1));title(sprintf('RGB Space\n\nRed'))
subplot(3,4,5);imshow(rgb_image(:,:,2));title('Green')
subplot(3,4,9);imshow(rgb_image(:,:,3));title('Blue')

% HSV
subplot(3,4,2);imshow(hsvim(:,:,1));title(sprintf('HSV Space\n\nHue'))
subplot(3,4,6);imshow(hsvim(:,:,2));title('Saturation')
subplot(3,4,10);imshow(hsvim(:,:,3));title('Brightness')

% YCbCr / YUV
subplot(3,4,3);imshow(yuvim(:,:,1));title(sprintf('YCbCr Space\n\nLuminance'))
subplot(3,4,7);imshow(yuvim(:,:,2));title('Blue Difference')
subplot(3,4,11);imshow(yuvim(:,:,3));title('Red Difference')

% CIELab
subplot(3,4,4);imshow(cieim(:,:,1));title(sprintf('CIELab Space\n\nLightness'))
subplot(3,4,8);imshow(cieim(:,:,2));title('Green-Red (a*)')
subplot(3,4,12);imshow(cieim(:,:,3));title('Yellow-Blue (b*)')


function CalculateHSVThreshold(rgb_image)
hsvim = rgb2hsv(rgb_image);  % Convert to HSV

% Extract relevant channels
hue_hsv = hsvim(:,:,1);
saturation_hsv = hsvim(:,:,2);
brightness_hsv = hsvim(:,:,3);

% Compute statistics
mean_hue = mean(hue_hsv(:));
std_hue = std(double(hue_hsv(:)));

mean_saturation = mean(saturation_hsv(:));
std_saturation = std(double(saturation_hsv(:)));

mean_brightness = mean(brightness_hsv(:));
std_brightness = std(double(brightness_hsv(:)));

% Choose k-factor for thresholding (adjustable)
k = 1.0;  % Increase if the threshold is too strict, decrease if too loose

function calculations(k)
% Calculate automatic thresholds
hue_min = max(0, (mean_hue - k * std_hue) * 180);
hue_max = min(179, (mean_hue + k * std_hue) * 180);

saturation_min = max(0, (mean_saturation - k * std_saturation) * 255);
saturation_max = min(255, (mean_saturation + k * std_saturation) * 255);

brightness_min = max(0, (mean_brightness - k * std_brightness) * 255);
brightness_max = min(255, (mean_brightness + k * std_brightness) * 255);

% Display calculated thresholds
fprintf('Calculated HSV Thresholds:\n');
fprintf('green_min = [%.0f, %.0f, %.0f]\n', hue_min, saturation_min, brightness_min);
fprintf('green_max = [%.0f, %.0f, %.0f]\n', hue_max, saturation_max, brightness_max);

% Plot histograms for better analysis
figure();
subplot(3,1,1); histogram(hue_hsv(:) * 180, 50); title('Hue Histogram'); xlim([0 180]);
subplot(3,1,2); histogram(saturation_hsv(:) * 255, 50); title('Saturation Histogram'); xlim([0 255]);
subplot(3,1,3); histogram(brightness_hsv(:) * 255, 50); title('Brightness Histogram'); xlim([0 255]);

% Suggest a mask preview (optional)
mask = (hue_hsv * 180 >= hue_min & hue_hsv * 180 <= hue_max) & ...
    (saturation_hsv * 255 >= saturation_min & saturation_hsv * 255 <= saturation_max) & ...
    (brightness_hsv * 255 >= brightness_min & brightness_hsv * 255 <= brightness_max);

figure();
imshow(mask);
title('Detected Green Areas (Binary Mask)');

