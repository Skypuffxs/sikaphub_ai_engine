<?php
require_once __DIR__ . '/parse_resume_client.php';

$extractedProfile = null;
$errorMessage = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['resume'])) {
    if ($_FILES['resume']['error'] === UPLOAD_ERR_OK) {
        $tmpPath = $_FILES['resume']['tmp_name'];
        $result = parseResumeWithAIEngine($tmpPath);
        
        if (isset($result['status']) && $result['status'] === 'success') {
            $extractedProfile = $result['profile'];
        } else {
            $errorMessage = $result['message'] ?? 'Failed to parse resume.';
        }
    } else {
        $errorMessage = 'File upload error code: ' . $_FILES['resume']['error'];
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>S.I.K.A.P. Hub - Background Profile Builder Test</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        h1 { color: #1e3a8a; font-size: 24px; margin-top: 0; }
        p.subtitle { color: #64748b; font-size: 14px; margin-bottom: 25px; }
        .upload-card { background: #eff6ff; border: 2px dashed #3b82f6; padding: 25px; border-radius: 8px; text-align: center; margin-bottom: 25px; }
        input[type="file"] { margin-bottom: 15px; }
        .btn { background: #2563eb; color: #fff; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; cursor: pointer; }
        .btn:hover { background: #1d4ed8; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: 600; color: #334155; margin-bottom: 5px; font-size: 14px; }
        input[type="text"], textarea { width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 5px; box-sizing: border-box; font-size: 14px; }
        textarea { height: 80px; }
        .error { background: #fef2f2; border: 1px solid #f87171; color: #991b1b; padding: 12px; border-radius: 5px; margin-bottom: 20px; }
        .success-banner { background: #f0fdf4; border: 1px solid #4ade80; color: #166534; padding: 12px; border-radius: 5px; margin-bottom: 20px; }
        .tag { display: inline-block; background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; margin: 2px; }
    </style>
</head>
<body>

<div class="container">
    <h1>S.I.K.A.P. Hub - Build Candidate Profile</h1>
    <p class="subtitle">Upload candidate CV/Resume. The AI Engine runs in the background to automatically populate your profile fields below.</p>

    <?php if ($errorMessage): ?>
        <div class="error">❌ <strong>Error:</strong> <?= htmlspecialchars($errorMessage) ?></div>
    <?php endif; ?>

    <?php if ($extractedProfile): ?>
        <div class="success-banner">✅ <strong>Success!</strong> Candidate profile fields auto-populated from resume in background.</div>
    <?php endif; ?>

    <!-- UPLOAD FORM -->
    <div class="upload-card">
        <form method="POST" enctype="multipart/form-data">
            <label for="resume"><strong>Upload Candidate Resume (PDF / DOCX):</strong></label><br>
            <input type="file" name="resume" id="resume" accept=".pdf,.docx" required><br>
            <button type="submit" class="btn">⚡ Upload & Auto-Fill Profile</button>
        </form>
    </div>

    <!-- PROFILE FORM -->
    <form style="margin-top: 20px;">
        <h3>Candidate Profile Information</h3>

        <div class="form-group">
            <label>Full Name</label>
            <input type="text" value="<?= htmlspecialchars($extractedProfile['name'] ?? '') ?>" placeholder="e.g. Juan Dela Cruz">
        </div>

        <div style="display: flex; gap: 15px;">
            <div class="form-group" style="flex: 1;">
                <label>Email Address</label>
                <input type="text" value="<?= htmlspecialchars($extractedProfile['contact']['email'] ?? '') ?>" placeholder="e.g. juan@email.com">
            </div>
            <div class="form-group" style="flex: 1;">
                <label>Phone Number</label>
                <input type="text" value="<?= htmlspecialchars($extractedProfile['contact']['phone'] ?? '') ?>" placeholder="e.g. 0912-345-6789">
            </div>
        </div>

        <div class="form-group">
            <label>Address / Location</label>
            <input type="text" value="<?= htmlspecialchars($extractedProfile['location']['address'] ?? '') ?>" placeholder="e.g. Guimba, Nueva Ecija">
        </div>

        <div class="form-group">
            <label>Career Objective / Summary</label>
            <textarea placeholder="Candidate objective..."><?= htmlspecialchars($extractedProfile['summary'] ?? '') ?></textarea>
        </div>

        <div class="form-group">
            <label>Extracted Skills Tags</label>
            <div>
                <?php 
                if (isset($extractedProfile['skills']['all_skills']) && !empty($extractedProfile['skills']['all_skills'])) {
                    foreach ($extractedProfile['skills']['all_skills'] as $skill) {
                        echo '<span class="tag">' . htmlspecialchars($skill) . '</span>';
                    }
                } else {
                    echo '<span style="color:#94a3b8; font-size:13px;">No skills extracted yet.</span>';
                }
                ?>
            </div>
        </div>

        <div class="form-group">
            <label>Education</label>
            <input type="text" value="<?= htmlspecialchars($extractedProfile['education'][0]['degree_or_level'] ?? '') ?>" placeholder="e.g. BS Information Technology">
        </div>
    </form>
</div>

</body>
</html>
