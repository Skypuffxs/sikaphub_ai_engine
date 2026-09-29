<?php
/**
 * S.I.K.A.P. Hub AI Engine - Business Permit Verification Client Helper
 * 
 * Call this function from your PHP (sikaphub_v2) controllers to send an uploaded
 * business permit document (PDF, PNG, JPG) for AI fraud detection & document verification.
 */

function verifyBusinessPermitWithAIEngine(
    $filePath,
    $expectedBusinessName = null,
    $expectedOwnerName = null,
    $aiEngineUrl = 'http://localhost:8000/verify-business-permit',
    $apiKey = null,
    $hmacSecret = null
) {
    if (!$apiKey) {
        $apiKey = getenv('AI_API_KEY') ?: 'cbfbbba77f15a06784742a72fe131ba083a7758fc0cb12db';
    }
    if (!$hmacSecret) {
        $hmacSecret = getenv('HMAC_SECRET') ?: 'e4d90f3b2a7c815e6b4f0a1c3d9e8b7f2a6c5d4e1b0f9a8c7d6e5f4b3a2c1d0e';
    }

    if (!file_exists($filePath)) {
        return ['status' => 'RED_FLAG', 'confidence_score' => 0.0, 'ai_feedback' => 'File not found on server: ' . $filePath];
    }

    $fileData = file_get_contents($filePath);
    $signature = hash_hmac('sha256', $fileData, $hmacSecret);
    $fileName = basename($filePath);

    $mimeType = 'application/octet-stream';
    if (function_exists('finfo_open')) {
        $finfo = finfo_open(FILEINFO_MIME_TYPE);
        $mimeType = finfo_file($finfo, $filePath);
        finfo_close($finfo);
    }

    $postData = [
        'file' => new CURLFile($filePath, $mimeType, $fileName)
    ];

    if ($expectedBusinessName) {
        $postData['expected_business_name'] = $expectedBusinessName;
    }
    if ($expectedOwnerName) {
        $postData['expected_owner_name'] = $expectedOwnerName;
    }

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $aiEngineUrl);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        "Authorization: Bearer {$apiKey}",
        "x-signature: {$signature}"
    ]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlError = curl_error($ch);
    curl_close($ch);

    if ($curlError) {
        return [
            'status' => 'RED_FLAG',
            'confidence_score' => 0.0,
            'ai_feedback' => "cURL Connection Error: {$curlError} (Ensure FastAPI AI Engine is running on port 8000)"
        ];
    }

    if ($httpCode !== 200) {
        return [
            'status' => 'RED_FLAG',
            'confidence_score' => 0.0,
            'ai_feedback' => "AI Engine HTTP {$httpCode}: {$response}"
        ];
    }

    return json_decode($response, true);
}
