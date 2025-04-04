% Clear workspace
clear all; close all; clc; clf

% Load the CSV file into a table
data = readtable('saved_data/hard_key_1.csv'); %-------CHANGE FILENAME----------
data = table2array(data);

counts_force = 2.4227;
counts_torque = 110.97; 

% Extract specific columns by index
time = data(:, 1); % First column (column 1)
fx = data(:, 2); % Second column (column 2)
fy = data(:, 3);
fz = data(:, 4);
tx = data(:, 5);
ty = data(:, 6);
tz = data(:, 7);

index = 10:length(time);



% check
% disp(time);

% Plotting Force vs Time
figure(1);
subplot(2,1,1)
title('Force vs Time');
hold on;
plot(time(index),fx(index),'-r','LineWidth',2);
plot(time(index),fy(index),'-g','LineWidth',2);
plot(time(index),fz(index),'-b','LineWidth',2);
xlabel('Time [s]'); ylabel('Force [N]')
legend('F_x', 'F_y','F_z','FontSize',16)
set(gca,'FontSize',16);
grid on;
ylim([-30, 30])
hold off;

subplot(2,1,2)
title('Torque vs Time');
hold on;
plot(time(index),tx(index),'-c','LineWidth',2);
plot(time(index),ty(index),'-m','LineWidth',2);
plot(time(index),tz(index),'-k','LineWidth',2);
xlabel('Time [s]'); ylabel('Torque [N]');
legend('T_x', 'T_y','T_z','FontSize',16)
set(gca,'FontSize',16);
ylim([-1, 1])
grid on;
hold off;



