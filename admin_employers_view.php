<?php
/**
 * View: Admin Employer Management Directory (with AI Permit Analytics & Feedback)
 * Place this file at: c:\xampp\htdocs\sikaphub_v2\app\views\admin\employers.php
 */
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Employer Directory | S.I.K.A.P. Hub Admin</title>
    <link rel="stylesheet" href="/sikaphub_v2/public/assets/css/theme.css">
    <script src="/sikaphub_v2/public/assets/js/tailwind.js"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: { primary: '#4338ca', 'primary-hover': '#3730a3', secondary: '#0d9488' }
                }
            }
        }
    </script>
</head>
<body class="bg-slate-100 min-h-screen pt-16 font-sans text-slate-800">

    <nav class="fixed top-0 left-0 right-0 h-16 bg-indigo-900 text-white flex items-center justify-between px-6 z-50 shadow-md">
        <a href="/sikaphub_v2/admin/dashboard" class="flex items-center gap-2.5 font-bold text-lg">
            <div class="w-7 h-7 rounded-md bg-white/20 flex items-center justify-center text-white">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3.5" y="3.5" width="17" height="17" rx="3" ry="3"></rect>
                    <rect x="8.5" y="8.5" width="7" height="7" rx="1.5" ry="1.5"></rect>
                </svg>
            </div>
            <span>SIKAPHUB</span> <span class="text-indigo-300 text-xs font-normal uppercase tracking-wider">Admin</span>
        </a>
        <div class="flex items-center gap-3 text-sm font-medium">
            <a href="/sikaphub_v2/admin/dashboard" class="px-3 py-1.5 rounded hover:bg-white/10">Dashboard</a>
            <a href="/sikaphub_v2/admin/employers" class="px-3 py-1.5 rounded bg-white/20 text-white">Employers</a>
            <a href="/sikaphub_v2/admin/seekers" class="px-3 py-1.5 rounded hover:bg-white/10">Seekers</a>
            <a href="/sikaphub_v2/admin/jobs" class="px-3 py-1.5 rounded hover:bg-white/10">Job Postings</a>
            <a href="/sikaphub_v2/admin/skills" class="px-3 py-1.5 rounded hover:bg-white/10">Skills</a>
            <a href="/sikaphub_v2/admin/audit-logs" class="px-3 py-1.5 rounded hover:bg-white/10">Audit Log</a>
            <a href="/sikaphub_v2/admin/logout" class="ml-4 px-3 py-1 border border-white/30 rounded hover:bg-white/10 text-xs">Logout</a>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto py-8 px-4 sm:px-6">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <div>
                <h1 class="text-2xl font-extrabold text-slate-900">Employer Management Directory</h1>
                <p class="text-slate-500 text-sm">Review, verify, and monitor all registered businesses with AI Permit Audit Analytics.</p>
            </div>
            <form method="GET" action="/sikaphub_v2/admin/employers" class="flex items-center gap-2">
                <input type="text" name="q" value="<?php echo htmlspecialchars($search); ?>" placeholder="Search company, contact..." class="px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary">
                <select name="status" class="px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:border-primary">
                    <option value="">All Statuses</option>
                    <option value="Pending" <?php echo $status === 'Pending' ? 'selected' : ''; ?>>Pending</option>
                    <option value="Verified" <?php echo $status === 'Verified' ? 'selected' : ''; ?>>Verified</option>
                    <option value="Rejected" <?php echo $status === 'Rejected' ? 'selected' : ''; ?>>Rejected</option>
                </select>
                <button type="submit" class="bg-primary text-white font-semibold px-4 py-2 rounded-lg text-sm hover:bg-primary-hover">Filter</button>
            </form>
        </div>

        <div class="bg-white rounded-2xl shadow border border-slate-200 overflow-hidden">
            <table class="w-full text-left text-sm text-slate-600">
                <thead class="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                    <tr>
                        <th class="p-4">Company Name</th>
                        <th class="p-4">Contact Details</th>
                        <th class="p-4">Business Permit & AI Analytics</th>
                        <th class="p-4">Status</th>
                        <th class="p-4">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <?php if (empty($employers)): ?>
                        <tr><td colspan="5" class="p-8 text-center text-slate-400">No employers found matching criteria.</td></tr>
                    <?php else: ?>
                        <?php foreach ($employers as $emp): ?>
                            <tr class="hover:bg-slate-50 border-b border-slate-100">
                                <td class="p-4">
                                    <div class="font-bold text-slate-900"><?php echo htmlspecialchars($emp['company_name']); ?></div>
                                    <div class="text-xs text-slate-400"><?php echo htmlspecialchars($emp['industry'] ?? 'General Industry'); ?></div>
                                </td>
                                <td class="p-4">
                                    <div class="font-medium text-slate-800"><?php echo htmlspecialchars($emp['contact_person'] ?? 'N/A'); ?></div>
                                    <div class="text-xs text-slate-500"><?php echo htmlspecialchars($emp['email'] ?? $emp['company_email'] ?? ''); ?></div>
                                    <div class="text-xs text-slate-400"><?php echo htmlspecialchars($emp['company_phone'] ?? ''); ?></div>
                                </td>
                                <td class="p-4">
                                    <?php if (!empty($emp['business_permit_file'])): ?>
                                        <div class="flex flex-col gap-1.5 items-start">
                                            <a href="/sikaphub_v2/admin/view-document?file=<?php echo urlencode($emp['business_permit_file']); ?>" target="_blank" class="inline-flex items-center gap-1 text-xs font-semibold text-primary bg-indigo-50 px-2.5 py-1 rounded border border-indigo-100 hover:bg-indigo-100">
                                                📄 View Permit
                                            </a>
                                            <?php
                                            $aiStatus = $emp['verification_status'] ?? 'pending';
                                            $aiBadgeClass = match($aiStatus) {
                                                'green_flag' => 'bg-emerald-50 text-emerald-700 border-emerald-200',
                                                'red_flag'   => 'bg-rose-50 text-rose-700 border-rose-200',
                                                default      => 'bg-slate-100 text-slate-600 border-slate-200'
                                            };
                                            $aiLabel = match($aiStatus) {
                                                'green_flag' => '🤖 AI Green Flag',
                                                'red_flag'   => '⚠️ AI Audit Flag',
                                                default      => '🤖 AI Review Pending'
                                            };
                                            ?>
                                            <button type="button" onclick="toggleAiAnalytics('emp-ai-<?php echo (int)$emp['employer_id']; ?>')" class="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded border <?php echo $aiBadgeClass; ?> hover:opacity-80 transition-opacity shadow-sm">
                                                <?php echo $aiLabel; ?> 📊
                                            </button>
                                        </div>
                                    <?php else: ?>
                                        <span class="text-xs text-slate-400">Not Uploaded</span>
                                    <?php endif; ?>
                                </td>
                                <td class="p-4">
                                    <?php
                                    $badge = match($emp['verified_status']) {
                                        'Verified' => 'bg-emerald-100 text-emerald-800 border-emerald-200',
                                        'Rejected' => 'bg-rose-100 text-rose-800 border-rose-200',
                                        default    => 'bg-amber-100 text-amber-800 border-amber-200'
                                    };
                                    ?>
                                    <span class="px-2.5 py-1 text-xs font-semibold rounded-full border <?php echo $badge; ?>">
                                        <?php echo htmlspecialchars($emp['verified_status']); ?>
                                    </span>
                                </td>
                                <td class="p-4">
                                    <form method="POST" action="/sikaphub_v2/admin/verify-employer" class="flex gap-2">
                                        <?php echo CSRF::csrfField(); ?>
                                        <input type="hidden" name="employer_id" value="<?php echo (int) $emp['employer_id']; ?>">
                                        <?php if ($emp['verified_status'] !== 'Verified'): ?>
                                            <button type="submit" name="status" value="Verified" class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-3 py-1.5 rounded transition-colors">
                                                Approve
                                            </button>
                                        <?php endif; ?>
                                        <?php if ($emp['verified_status'] !== 'Rejected'): ?>
                                            <button type="submit" name="status" value="Rejected" class="bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs px-3 py-1.5 rounded transition-colors">
                                                Reject
                                            </button>
                                        <?php endif; ?>
                                    </form>
                                </td>
                            </tr>

                            <!-- AI Analytics Expandable Panel -->
                            <tr id="emp-ai-<?php echo (int)$emp['employer_id']; ?>" class="hidden bg-slate-50/80 border-b border-slate-200">
                                <td colspan="5" class="p-4">
                                    <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm space-y-3">
                                        <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                                            <div class="flex items-center gap-2">
                                                <span class="text-base">🤖</span>
                                                <h4 class="font-bold text-slate-900 text-sm">AI Engine Business Permit Audit & Analytics</h4>
                                                <span class="text-xs px-2 py-0.5 rounded font-semibold <?php echo $aiBadgeClass; ?>">
                                                    <?php echo strtoupper($aiStatus); ?>
                                                </span>
                                            </div>
                                            <button type="button" onclick="toggleAiAnalytics('emp-ai-<?php echo (int)$emp['employer_id']; ?>')" class="text-xs text-slate-400 hover:text-slate-600 font-bold">✕ Close</button>
                                        </div>

                                        <!-- AI Feedback Rationale -->
                                        <div>
                                            <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">AI Audit Rationale & Feedback</div>
                                            <div class="text-xs bg-slate-50 p-3 rounded-lg text-slate-800 font-sans leading-relaxed border border-slate-200">
                                                <?php echo htmlspecialchars($emp['ai_feedback'] ?? 'No AI feedback recorded for this permit yet.'); ?>
                                            </div>
                                        </div>

                                        <!-- Parsed Fields Grid -->
                                        <?php
                                        $extracted = [];
                                        if (!empty($emp['extracted_permit_data'])) {
                                            $decoded = json_decode($emp['extracted_permit_data'], true);
                                            if (is_array($decoded)) {
                                                $extracted = $decoded;
                                            }
                                        }
                                        ?>
                                        <?php if (!empty($extracted)): ?>
                                            <div>
                                                <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Parsed Permit Details</div>
                                                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                                                    <div class="bg-indigo-50/60 p-2.5 rounded-lg border border-indigo-100">
                                                        <div class="text-slate-400 text-[10px] uppercase font-bold">Business Name</div>
                                                        <div class="font-bold text-slate-800 mt-0.5"><?php echo htmlspecialchars($extracted['business_name'] ?? 'N/A'); ?></div>
                                                    </div>
                                                    <div class="bg-indigo-50/60 p-2.5 rounded-lg border border-indigo-100">
                                                        <div class="text-slate-400 text-[10px] uppercase font-bold">Permit / Reg Number</div>
                                                        <div class="font-bold text-slate-800 mt-0.5"><?php echo htmlspecialchars($extracted['permit_number'] ?? 'N/A'); ?></div>
                                                    </div>
                                                    <div class="bg-indigo-50/60 p-2.5 rounded-lg border border-indigo-100">
                                                        <div class="text-slate-400 text-[10px] uppercase font-bold">Expiry Date</div>
                                                        <div class="font-bold text-slate-800 mt-0.5"><?php echo htmlspecialchars($extracted['expiry_date'] ?? 'N/A'); ?></div>
                                                    </div>
                                                    <div class="bg-indigo-50/60 p-2.5 rounded-lg border border-indigo-100">
                                                        <div class="text-slate-400 text-[10px] uppercase font-bold">Issuing Authority</div>
                                                        <div class="font-bold text-slate-800 mt-0.5"><?php echo htmlspecialchars($extracted['issuing_authority'] ?? 'N/A'); ?></div>
                                                    </div>
                                                </div>
                                            </div>
                                        <?php endif; ?>
                                    </div>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </main>

    <script>
        function toggleAiAnalytics(rowId) {
            const el = document.getElementById(rowId);
            if (el) {
                el.classList.toggle('hidden');
            }
        }
    </script>
</body>
</html>
