function ViewColorSpaces_V2
    rgbim = imread('test_moments\latest_frame_original_Intersection_2.jpg');
    ViewColorSpaces2(rgbim);
    AnalyzeGreenMarkers(rgbim);
end

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
end

function AnalyzeGreenMarkers(rgb_image)
    hsvim = rgb2hsv(rgb_image);
    yuvim = rgb2ycbcr(rgb_image);
    
    % Convert to CIELab
    cform = makecform('srgb2lab');
    cieim = applycform(rgb_image, cform);
    
    % Extract green-related channels
    green_rgb = rgb_image(:,:,2);
    hue_hsv = hsvim(:,:,1);
    saturation_hsv = hsvim(:,:,2);
    green_red_cielab = cieim(:,:,2);
    
    % Compute statistics
    mean_green = mean(green_rgb(:));
    std_green = std(double(green_rgb(:)));

    mean_hue = mean(hue_hsv(:));
    std_hue = std(double(hue_hsv(:)));

    mean_saturation = mean(saturation_hsv(:));
    std_saturation = std(double(saturation_hsv(:)));

    mean_greenred = mean(green_red_cielab(:));
    std_greenred = std(double(green_red_cielab(:)));

    % Display results
    fprintf('Mean & Std Dev:\n');
    fprintf('RGB Green: Mean = %.2f, Std = %.2f\n', mean_green, std_green);
    fprintf('HSV Hue: Mean = %.2f, Std = %.2f\n', mean_hue, std_hue);
    fprintf('HSV Saturation: Mean = %.2f, Std = %.2f\n', mean_saturation, std_saturation);
    fprintf('CIELab Green-Red: Mean = %.2f, Std = %.2f\n', mean_greenred, std_greenred);
    
    % Plot histograms
    figure();
    subplot(2,2,1); histogram(green_rgb(:), 256); title('RGB Green Histogram');
    subplot(2,2,2); histogram(hue_hsv(:), 256); title('HSV Hue Histogram');
    subplot(2,2,3); histogram(saturation_hsv(:), 256); title('HSV Saturation Histogram');
    subplot(2,2,4); histogram(green_red_cielab(:), 256); title('CIELab Green-Red Histogram');

    % Automatic threshold suggestion
    suggested_threshold = mean_hue + std_hue;
    fprintf('Suggested Green Detection Hue Threshold: %.2f\n', suggested_threshold);
end
