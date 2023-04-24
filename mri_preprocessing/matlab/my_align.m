function [out] = my_align(P, output_folder, only_rigid)
% Modified from 
%     https://github.com/WTCN-computational-anatomy-group/Patient-Preprocessing
% Reposition an image by affine aligning to MNI space and Procrustes adjustment
% FORMAT align(P)
% INPUT
% P - name of NIfTI image
% only_rigid - true to only keep the rigid transformation
% OUTPUT
% M - Rigid or Affine matrix (determined by only_rigid) 
%
% OBS: Image will have the matrix in its header adjusted.
%__________________________________________________________________________
% Copyright (C) 2018 Wellcome Trust Centre for Neuroimaging

if ~isfile(P)
   out.rigid = NaN;
   out.affine = NaN;
   disp([P " does not exist"]);
   return
end

[input_dir, input_fname, input_ext] = fileparts(convertStringsToChars(P));
if nargin < 2
    output_folder = convertStringsToChars(input_dir);
end
if nargin < 3, only_rigid = false; end

% Just to deal with matlab / spm weird path handling ...
P = convertStringsToChars(P);
% input_fname = convertStringsToChars(input_fname);
% input_ext = convertStringsToChars(input_ext);
% output_folder = convertStringsToChars(output_folder);

% Load tissue probability data
tpm = fullfile(spm('dir'),'tpm','TPM.nii,');
tpm = [repmat(tpm,[6 1]) num2str((1:6)')];
tpm = spm_load_priors8(tpm);

% Do the affine registration
%V = spm_vol(P);
V = nifti(P);

M               = V(1).mat;
c               = (V(1).dim+1)/2;
V(1).mat(1:3,4) = -M(1:3,1:3)*c(:);
[Affine1,ll1]   = spm_maff8(V(1),8,(0+1)*16,tpm,[],'mni'); % Closer to rigid
Affine1         = Affine1*(V(1).mat/M);

% Run using the origin from the header
V(1).mat      = M;
[Affine2,ll2] = spm_maff8(V(1),8,(0+1)*16,tpm,[],'mni'); % Closer to rigid

% Pick the result with the best fit
if ll1>ll2
    Affine  = Affine1; 
else
    Affine  = Affine2;
end

Affine = spm_maff8(P,2,32,tpm,Affine,'mni'); % Heavily regularised
Affine = spm_maff8(P,2,1 ,tpm,Affine,'mni'); % Lightly regularised

% Generate mm coordinates of where deformations map from
x      = affind(rgrid(size(tpm.dat{1})),tpm.M);

% Generate mm coordinates of where deformation maps to
y1     = affind(x,inv(Affine));

% Weight the transform via GM+WM
weight = single(exp(tpm.dat{1})+exp(tpm.dat{2}));

% Weighted Procrustes analysis
[Affine, R]  = spm_get_closest_affine(x,y1,weight);

% Load header
header_rigid = spm_vol(P);
header_affine = spm_vol(P);
data = spm_read_vols(header_rigid);

header_rigid.mat = R\header_rigid.mat;
header_rigid.fname = fullfile(output_folder, ['rigid_' input_fname input_ext]);
disp(header_rigid);
spm_write_vol(header_rigid, data);
out.rigid = header_rigid.fname;
if only_rigid
    out.affine = NaN;
else
    header_affine.mat = Affine\header_affine.mat;
    header_affine.fname = fullfile(output_folder, ['affine_' input_fname input_ext]);
    spm_write_vol(header_affine, data);
    out.affine = header_affine.fname;
end

% Invert
% R      = inv(R);

% Write the new matrix to the header
% Nii.mat = M\Nii.mat;
% create(Nii);
%==========================================================================

%==========================================================================
function x = rgrid(d)
x = zeros([d(1:3) 3],'single');
[x1,x2] = ndgrid(single(1:d(1)),single(1:d(2)));
for i=1:d(3)
    x(:,:,i,1) = x1;
    x(:,:,i,2) = x2;
    x(:,:,i,3) = single(i);
end
%==========================================================================

%==========================================================================
function y1 = affind(y0,M)
y1 = zeros(size(y0),'single');
for d=1:3
    y1(:,:,:,d) = y0(:,:,:,1)*M(d,1) + y0(:,:,:,2)*M(d,2) + y0(:,:,:,3)*M(d,3) + M(d,4);
end
%==========================================================================