% Clear workspace
clear all; close all; clc;

% Load the CSV file into a table
data = readtable('ascii_data_fz_t1.csv'); %-------CHANGE FILENAME----------
data = table2array(data);

% Extract specific columns by index
time = data(:, 1); % First column (column 1)
fx = data(:, 2); % Second column (column 2)
fy = data(:, 3);
fz = data(:, 4);
tx = data(:, 5);
ty = data(:, 6);
tz = data(:, 7);

% check
% disp(time);

% Plotting Force vs Time
figure(1);
title('Force vs Time');
hold on;
plot(time,fx,'-r','LineWidth',3);
plot(time,fy,'-g','LineWidth',3);
plot(time,fz,'-b','LineWidth',3);
xlabel('Time [s]'); ylabel('Force [N]')
legend('F_x', 'F_y','F_z','FontSize',16)
set(gca,'FontSize',16);
grid on;
hold off;

figure(2); 
title('Torque vs Time');
hold on;
plot(time,tx,'-c','LineWidth',3);
plot(time,ty,'-m','LineWidth',3);
plot(time,tz,'-k','LineWidth',3);
xlabel('Time [s]'); ylabel('Torque [N]');
legend('T_x', 'T_y','T_z','FontSize',16)
set(gca,'FontSize',16);
grid on;
hold off;



