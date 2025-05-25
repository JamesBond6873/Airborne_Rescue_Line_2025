function AutoThresholding
    % Read the RGB image
    rgbImage = imread('test_moments\latest_frame_original_Intersection_2.jpg');

    % Convert RGB to HSV correctly
    hsvImage = rgb2hsv(rgbImage);

    % Extract individual channels
    hue = hsvImage(:,:,1) * 180;        % Scale to 0-180
    saturation = hsvImage(:,:,2) * 255; % Scale to 0-255
    brightness = hsvImage(:,:,3) * 255; % Scale to 0-255

    % Compute statistics
    hueMean = mean(hue(:));
    hueStd = std(hue(:));
    saturationMean = mean(saturation(:));
    saturationStd = std(saturation(:));

    % Print statistics
    fprintf('Hue: Mean = %.2f, Std = %.2f\n', hueMean, hueStd);
    fprintf('Saturation: Mean = %.2f, Std = %.2f\n', saturationMean, saturationStd);

    % Define k-values to test
    kValues = [0.5, 1.0, 1.10, 1.20, 1.30, 1.40, 1.5, 1.6,1.7,1.8,1.9 2.0, 2.5];

    % Create a figure for the results
    figure;
    for i = 1:length(kValues)
        k = kValues(i);

        % Compute dynamic thresholds using k-factor
        hueMin = max(0, hueMean - k * hueStd);
        hueMax = min(180, hueMean + k * hueStd);
        satMin = max(0, saturationMean - k * saturationStd);
        satMax = min(255, saturationMean + k * saturationStd);

        % Apply thresholding for green detection
        greenMask = (hue >= hueMin & hue <= hueMax) & ...
                    (saturation >= satMin & saturation <= satMax);

        % Show results
        subplot(2, ceil(length(kValues)/2), i);
        imshow(greenMask);
        title(sprintf('k = %.1f', k));
    end
    suptitle('Green Area Detection for Different k-values');

    % Show histograms for analysis
    figure;
    subplot(3,1,1);
    histogram(hue, 50); title('Hue Histogram'); xlabel('Hue (0-180)'); ylabel('Count');
    
    subplot(3,1,2);
    histogram(saturation, 50); title('Saturation Histogram'); xlabel('Saturation (0-255)'); ylabel('Count');
    
    subplot(3,1,3);
    histogram(brightness, 50); title('Brightness Histogram'); xlabel('Brightness (0-255)'); ylabel('Count');
end
