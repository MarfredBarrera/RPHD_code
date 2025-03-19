% Clear workspace
clc; clear; close all;

%% Linear Regression for Mini45 Force Test

% Define the data
force = [0.04, 0.100, 0.200, 0.300, 0.400, 0.500, 2, 2.44, 2+2.44]*9.81;  % Force in N
counts = [1, 2.333, 4, 7.333, 8.333, 14, 48.5, 58.667, 105];  % Average counts

% Perform linear regression (degree 1 polynomial)
p = polyfit(force, counts, 1);

% Display the results
slope = p(1);  % The slope of the regression line
intercept = p(2);  % The intercept of the regression line

% Display the regression line parameters
disp(['Slope: ', num2str(slope)]);
disp(['Intercept: ', num2str(intercept)]);

% Create a scatter plot of the data
scatter(force, counts,200,'filled');
figure(1);
hold on;

% Define a range of x values (weights) for plotting the regression line
x_values = linspace(min(force), max(force), 100);  % Create a vector of x values

% Calculate the corresponding y values (counts) using polyval
y_values = polyval(p, x_values);  % Evaluate the linear regression at the x values

% Plot the regression line
plot(x_values, y_values, 'r-', 'LineWidth', 5);
xlabel('Force (N)');
ylabel('Average Count');
title('Linear Regression: Force vs. Average Count','FontSize',20);
legend('Data Points', 'Regression Line','FontSize',20);
set(gca,'FontSize',20);
grid on;
hold off;

%% Linear Regression for Mini45 Torque Test

% Define the data
torque = ([0.100, 0.200, 0.300, 0.400]*9.81)*0.23;  % Torque in Nm
counts = [25.4, 50, 76.6, 100];  % Average counts

% Perform linear regression (degree 1 polynomial)
p = polyfit(torque, counts, 1);

% Display the results
slope = p(1);  % The slope of the regression line
intercept = p(2);  % The intercept of the regression line

% Display the regression line parameters
disp(['Slope: ', num2str(slope)]);
disp(['Intercept: ', num2str(intercept)]);

% Create a scatter plot of the data
figure(2);
scatter(torque, counts,200,'filled');
hold on;

% Define a range of x values (torque) for plotting the regression line
x_values = linspace(min(torque), max(torque), 100);  % Create a vector of x values

% Calculate the corresponding y values (counts) using polyval
y_values = polyval(p, x_values);  % Evaluate the linear regression at the x values

% Plot the regression line
plot(x_values, y_values, 'r-', 'LineWidth', 5);
xlabel('Torque (Nm)');
ylabel('Average Count');
title('Linear Regression: Torque vs. Average Count','FontSize',20);
legend('Data Points', 'Regression Line','FontSize',20);
set(gca,'FontSize',20);
grid on;
hold off;