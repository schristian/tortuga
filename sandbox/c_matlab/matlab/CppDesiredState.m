function convertedDesiredState = CppDesiredState(DesiredState, too_from)

% We are converting from Matlab to CPP format
if too_from == 1
    q = DesiredState.quaternion;
    w = DesiredState.angularRate;
    
    % Convert static array to individual numbers (HACK!)
    convertedDesiredState = struct('speed',DesiredState.speed, ...
        'depth',DesiredState.depth, ...
        'q0', q(1), 'q1', q(2), 'q2', q(3), 'q3', q(4),  ...
        'w0', w(1), 'w1', w(2), 'w2', w(3));
% Converting from 
else
    convertedDesiredState = struct('speed', DesiredState.speed, ...
        'depth', DesiredState.depth,...
        'quaternion', [DesiredState.q0 DesiredState.q1 DesiredState.q2 DesiredState.q3]',...
        'angularRate',[DesiredState.w0 DesiredState.w1 DesiredState.w2]');
end