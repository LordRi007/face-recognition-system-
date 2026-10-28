// ==========================================================================
// Face Recognition Management System (FRMS) - Internationalization (i18n)
// English (en) & Khmer (km - ភាសាខ្មែរ) Language Translation Engine
// ==========================================================================

const TRANSLATIONS = {
  en: {
    // Navigation & Layout
    "Overview": "Overview",
    "Dashboard": "Dashboard",
    "Biometrics & AI": "Biometrics & AI",
    "Face Enrollment": "Face Enrollment",
    "Face Verification": "Face Verification",
    "Face Mood & Feeling": "Face Mood & Feeling",
    "Attendance": "Attendance",
    "Today's Attendance": "Today's Attendance",
    "Attendance History": "Attendance History",
    "People & Org": "People & Org",
    "User Directory": "User Directory",
    "Add User": "Add User",
    "Analytics & Wellness": "Analytics & Wellness",
    "Reports & Analytics": "Reports & Analytics",
    "Mood & Wellness": "Mood & Wellness",
    "System & Security": "System & Security",
    "Audit Trail": "Audit Trail",
    "Verification Logs": "Verification Logs",
    "System Settings": "System Settings",
    "Privacy & Consent": "Privacy & Consent",
    "AES-256 Biometric Encrypted": "AES-256 Biometric Encrypted",
    "My Profile": "My Profile",
    "Sign Out": "Sign Out",
    "Sign In": "Sign In",
    "Welcome to": "Welcome to",
    "Face Recognition & Identity Management System": "Face Recognition & Identity Management System",
    "Email Address": "Email Address",
    "Password": "Password",
    "Keep me signed in": "Keep me signed in",
    "Authenticate": "Authenticate",
    "Forgot password?": "Forgot password?",
    "Privacy Policy": "Privacy Policy",
    "System Operational": "System Operational",
    "All rights reserved.": "All rights reserved.",
    "Default Development Credentials:": "Default Development Credentials:",

    // Dashboard
    "Total Registered Users": "Total Registered Users",
    "Faces Enrolled": "Faces Enrolled",
    "On Time": "On Time",
    "Late": "Late",
    "Absent": "Absent",
    "Quick Actions": "Quick Actions",
    "Live Facial Recognition": "Live Facial Recognition",
    "Attendance Log": "Attendance Log",
    "User Management": "User Management",
    "Recent Attendance Activity": "Recent Attendance Activity",
    "View All Attendance": "View All Attendance",
    "Biometric Coverage": "Biometric Coverage",
    "System Health": "System Health",

    // 1-to-1 Verification Page
    "1-to-1 Identity Verification": "1-to-1 Identity Verification",
    "Claimed Identity (1-to-1 Verification)": "Claimed Identity (1-to-1 Verification)",
    "Biometric Status:": "Biometric Status:",
    "Checking...": "Checking...",
    "Enrolled (Ready)": "Enrolled (Ready)",
    "No Face Enrolled": "No Face Enrolled",
    "Live Webcam": "Live Webcam",
    "Image Upload": "Image Upload",
    "Alternative PIN Fallback": "Alternative PIN Fallback",
    "Camera Standby": "Camera Standby",
    "Connecting camera...": "Connecting camera...",
    "Look directly into the camera. Hold steady.": "Look directly into the camera. Hold steady.",
    "Auto-Scan Active: Look into camera to verify": "Auto-Scan Active: Look into camera to verify",
    "Auto-Scanning: Looking for face...": "Auto-Scanning: Looking for face...",
    "Face Aligned! Verifying biometrics...": "Face Aligned! Verifying biometrics...",
    "Verified:": "Verified:",
    "Scan Again": "Scan Again",
    "Live Auto-Scanning": "Live Auto-Scanning",
    "Verification Result": "Verification Result",
    "Position your face inside the oval guide. The system will automatically detect and verify your identity.": "Position your face inside the oval guide. The system will automatically detect and verify your identity.",
    "Identity Confirmed!": "Identity Confirmed!",
    "Verification Failed": "Verification Failed",
    "Biometric Similarity:": "Biometric Similarity:",
    "Cosine Distance:": "Cosine Distance:",
    "ArcFace Threshold:": "ArcFace Threshold:",
    "Record Check-In": "Record Check-In",
    "Record Check-Out": "Record Check-Out",
    "Non-Biometric PIN Verification": "Non-Biometric PIN Verification",
    "For users with camera issues or those who have opted out of facial biometrics.": "For users with camera issues or those who have opted out of facial biometrics.",
    "Enter 4-6 Digit User PIN": "Enter 4-6 Digit User PIN",
    "Verify PIN & Check In": "Verify PIN & Check In",
    "Upload Image for 1-to-1 Verification": "Upload Image for 1-to-1 Verification",
    "Select a clear, front-facing image (JPEG or PNG, max 16MB) to verify against the claimed user template.": "Select a clear, front-facing image (JPEG or PNG, max 16MB) to verify against the claimed user template.",
    "Verify Uploaded Image": "Verify Uploaded Image",
    "Claimed user has no face enrolled": "Claimed user has no face enrolled",
    "Multiple faces detected. 1 person only.": "Multiple faces detected. 1 person only.",

    // Face Biometric Enrollment
    "Face Biometric Enrollment": "Face Biometric Enrollment",
    "Informed Biometric Consent Notice": "Informed Biometric Consent Notice",
    "I have read, understood, and voluntarily agree to the biometric enrollment policy.": "I have read, understood, and voluntarily agree to the biometric enrollment policy.",
    "Live Camera Feed": "Live Camera Feed",
    "Center face within the oval. Ensure even lighting.": "Center face within the oval. Ensure even lighting.",
    "Capture & Enroll Face": "Capture & Enroll Face",
    "Target Identity": "Target Identity",
    "Enrollment Quality Checks": "Enrollment Quality Checks",
    "Face Count:": "Face Count:",
    "Image Sharpness (Blur Metric):": "Image Sharpness (Blur Metric):",
    "Illumination (Brightness):": "Illumination (Brightness):",
    "Requires ≥ 70.0 Laplacian variance.": "Requires ≥ 70.0 Laplacian variance.",
    "Optimal range: 40 - 225 mean grayscale.": "Optimal range: 40 - 225 mean grayscale.",
    "Must be exactly 1 face in camera frame.": "Must be exactly 1 face in camera frame.",

    // Mood & Feeling Tracker
    "Live AI Face Mood & Affective Telemetry": "Live AI Face Mood & Affective Telemetry",
    "AI Emotional & Wellness Telemetry": "AI Emotional & Wellness Telemetry",
    "Auto-Capture Snapshot": "Auto-Capture Snapshot",
    "Snapshot Mode:": "Snapshot Mode:",
    "1 per unique person": "1 per unique person",
    "Reset Captured Persons": "Reset Captured Persons",
    "Log Manual Check-In": "Log Manual Check-In",
    "Recent Emotion & Mood Check-Ins": "Recent Emotion & Mood Check-Ins",
    "Awaiting Face...": "Awaiting Face...",
    "Dominant Emotion": "Dominant Emotion",
    "Valence (Pleasantness)": "Valence (Pleasantness)",
    "Arousal (Energy)": "Arousal (Energy)",
    "Emotion Breakdown": "Emotion Breakdown",
    "Recommended Wellness Action": "Recommended Wellness Action",
    "Time": "Time",
    "Photo": "Photo",
    "Feeling / Mood": "Feeling / Mood",
    "Confidence": "Confidence",
    "Valence": "Valence",
    "Energy": "Energy",
    "Context": "Context",
    "Note": "Note",

    // Attendance Kiosk & Logs
    "Live Attendance Kiosk": "Live Attendance Kiosk",
    "Mark Attendance": "Mark Attendance",
    "Check In": "Check In",
    "Check Out": "Check Out",
    "Employee": "Employee",
    "Timestamp": "Timestamp",
    "Verification Method": "Verification Method",
    "Facial Recognition": "Facial Recognition",
    "PIN Verification": "PIN Verification",
    "Manual Override": "Manual Override",

    // Users Management
    "Add New User": "Add New User",
    "Edit User": "Edit User",
    "Full Name": "Full Name",
    "Email": "Email",
    "Biometric Status": "Biometric Status",
    "Active": "Active",
    "Inactive": "Inactive",
    "Delete User": "Delete User",
    "Enroll Face": "Enroll Face",
    "Re-enroll Face": "Re-enroll Face",

    // Profile & Common
    "Personal Information": "Personal Information",
    "Change Password": "Change Password",
    "Current Password": "Current Password",
    "New Password": "New Password",
    "Confirm New Password": "Confirm New Password",
    "Update Profile": "Update Profile",
    "Set Alternative PIN": "Set Alternative PIN",
    "Update PIN": "Update PIN",
    "Alternative Non-Biometric PIN": "Alternative Non-Biometric PIN",
    "PIN Active": "PIN Active",
    "Not Configured": "Not Configured",
    "Configure a 4 to 6 digit numerical PIN to verify your identity and mark attendance whenever the camera is unavailable or if you choose not to use facial recognition.": "Configure a 4 to 6 digit numerical PIN to verify your identity and mark attendance whenever the camera is unavailable or if you choose not to use facial recognition.",
    "Save": "Save",
    "Cancel": "Cancel",
    "Close": "Close",
    "Filter": "Filter",
    "Export": "Export",
    "Success!": "Success!",
    "Error": "Error",
    "Warning": "Warning",
    "Department": "Department",
    "Role": "Role",
    "Status": "Status",
    "Actions": "Actions",
    "Name": "Name",
    "Date": "Date"
  },

  km: {
    // Navigation & Layout
    "Overview": "ទិដ្ឋភាពទូទៅ",
    "Dashboard": "ផ្ទាំងគ្រប់គ្រង",
    "Biometrics & AI": "ជីវមាត្រ & AI",
    "Face Enrollment": "ចុះឈ្មោះទម្រង់មុខ",
    "Face Verification": "ផ្ទៀងផ្ទាត់ទម្រង់មុខ",
    "Face Mood & Feeling": "អារម្មណ៍ & អាកប្បកិរិយាមុខ",
    "Attendance": "វត្តមាន",
    "Today's Attendance": "វត្តមានថ្ងៃនេះ",
    "Attendance History": "ប្រវត្តិវត្តមាន",
    "People & Org": "បុគ្គលិក & អង្គភាព",
    "User Directory": "បញ្ជីឈ្មោះអ្នកប្រើប្រាស់",
    "Add User": "បន្ថែមអ្នកប្រើប្រាស់",
    "Analytics & Wellness": "ស្ថិតិ & សុខុមាលភាព",
    "Reports & Analytics": "របាយការណ៍ & ស្ថិតិ",
    "Mood & Wellness": "អារម្មណ៍ & សុខុមាលភាព",
    "System & Security": "ប្រព័ន្ធ & សុវត្ថិភាព",
    "Audit Trail": "កំណត់ហេតុត្រួតពិនិត្យ",
    "Verification Logs": "កំណត់ហេតុផ្ទៀងផ្ទាត់",
    "System Settings": "ការកំណត់ប្រព័ន្ធ",
    "Privacy & Consent": "ភាពឯកជន & ការយល់ព្រម",
    "AES-256 Biometric Encrypted": "អ៊ិនគ្រីបជីវមាត្រ AES-256",
    "My Profile": "គណនីផ្ទាល់ខ្លួន",
    "Sign Out": "ចាកចេញ",
    "Sign In": "ចូលគណនី",
    "Welcome to": "សូមស្វាគមន៍មកកាន់",
    "Face Recognition & Identity Management System": "ប្រព័ន្ធសម្គាល់ទម្រង់មុខ និងគ្រប់គ្រងអត្តសញ្ញាណ",
    "Email Address": "អាសយដ្ឋានអ៊ីមែល",
    "Password": "ពាក្យសម្ងាត់",
    "Keep me signed in": "ចងចាំការចូលរបស់ខ្ញុំ",
    "Authenticate": "ផ្ទៀងផ្ទាត់ចូល",
    "Forgot password?": "ភ្លេចពាក្យសម្ងាត់?",
    "Privacy Policy": "គោលការណ៍ឯកជនភាព",
    "System Operational": "ប្រព័ន្ធដំណើរការធម្មតា",
    "All rights reserved.": "រក្សាសិទ្ធិគ្រប់យ៉ាង។",
    "Default Development Credentials:": "គណនីសាកល្បងលំនាំដើម:",

    // Dashboard
    "Total Registered Users": "អ្នកប្រើប្រាស់បានចុះឈ្មោះសរុប",
    "Faces Enrolled": "បានចុះឈ្មោះទម្រង់មុខ",
    "On Time": "ទាន់ពេល",
    "Late": "យឺត",
    "Absent": "អវត្តមាន",
    "Quick Actions": "សកម្មភាពរហ័ស",
    "Live Facial Recognition": "ការសម្គាល់ទម្រង់មុខផ្ទាល់",
    "Attendance Log": "កំណត់ហេតុវត្តមាន",
    "User Management": "ការគ្រប់គ្រងអ្នកប្រើប្រាស់",
    "Recent Attendance Activity": "សកម្មភាពវត្តមានថ្មីៗ",
    "View All Attendance": "មើលវត្តមានទាំងអស់",
    "Biometric Coverage": "ការគ្របដណ្តប់ជីវមាត្រ",
    "System Health": "ស្ថានភាពសុខភាពប្រព័ន្ធ",

    // 1-to-1 Verification Page
    "1-to-1 Identity Verification": "ការផ្ទៀងផ្ទាត់អត្តសញ្ញាណ 1-to-1",
    "Claimed Identity (1-to-1 Verification)": "អត្តសញ្ញាណដែលអះអាង (ការផ្ទៀងផ្ទាត់ 1-to-1)",
    "Biometric Status:": "ស្ថានភាពជីវមាត្រ:",
    "Checking...": "កំពុងពិនិត្យ...",
    "Enrolled (Ready)": "បានចុះឈ្មោះ (រួចរាល់)",
    "No Face Enrolled": "មិនទាន់មានទម្រង់មុខ",
    "Live Webcam": "កាមេរ៉ាផ្ទាល់",
    "Image Upload": "បញ្ចូលរូបភាព",
    "Alternative PIN Fallback": "ប្រើលេខកូដ PIN ជំនួស",
    "Camera Standby": "កាមេរ៉ារង់ចាំ",
    "Connecting camera...": "កំពុងភ្ជាប់កាមេរ៉ា...",
    "Look directly into the camera. Hold steady.": "សូមមើលចំកាមេរ៉ា និងរក្សាជំហរនឹង។",
    "Auto-Scan Active: Look into camera to verify": "ការស្កេនស្វ័យប្រវត្តិកំពុងដំណើរការ: សូមមើលកាមេរ៉ាដើម្បីផ្ទៀងផ្ទាត់",
    "Auto-Scanning: Looking for face...": "កំពុងស្កេនស្វ័យប្រវត្តិ: កំពុងស្វែងរកមុខ...",
    "Face Aligned! Verifying biometrics...": "បានសម្គាល់មុខ! កំពុងផ្ទៀងផ្ទាត់ជីវមាត្រ...",
    "Verified:": "បានផ្ទៀងផ្ទាត់:",
    "Scan Again": "ស្កេនម្តងទៀត",
    "Live Auto-Scanning": "ការស្កេនស្វ័យប្រវត្តិផ្ទាល់",
    "Verification Result": "លទ្ធផលនៃការផ្ទៀងផ្ទាត់",
    "Position your face inside the oval guide. The system will automatically detect and verify your identity.": "សូមដាក់មុខរបស់អ្នកក្នុងរង្វង់ណែនាំ។ ប្រព័ន្ធនឹងរកឃើញ និងផ្ទៀងផ្ទាត់អត្តសញ្ញាណដោយស្វ័យប្រវត្តិ។",
    "Identity Confirmed!": "អត្តសញ្ញាណត្រូវបានបញ្ជាក់ជោគជ័យ!",
    "Verification Failed": "ការផ្ទៀងផ្ទាត់មិនជោគជ័យ",
    "Biometric Similarity:": "កម្រិតស្រដៀងគ្នានៃជីវមាត្រ:",
    "Cosine Distance:": "ចម្ងាយ Cosine:",
    "ArcFace Threshold:": "កម្រិតកំណត់ ArcFace:",
    "Record Check-In": "កត់ត្រាវត្តមានចូល",
    "Record Check-Out": "កត់ត្រាវត្តមានចេញ",
    "Non-Biometric PIN Verification": "ការផ្ទៀងផ្ទាត់លេខកូដ PIN មិនមែនជីវមាត្រ",
    "For users with camera issues or those who have opted out of facial biometrics.": "សម្រាប់អ្នកប្រើប្រាស់ដែលមានបញ្ហាកាមេរ៉ា ឬអ្នកដែលបានបដិសេធជីវមាត្រទម្រង់មុខ។",
    "Enter 4-6 Digit User PIN": "បញ្ចូលលេខកូដ PIN 4-6 ខ្ទង់",
    "Verify PIN & Check In": "ផ្ទៀងផ្ទាត់ PIN & កត់ត្រាវត្តមាន",
    "Upload Image for 1-to-1 Verification": "បញ្ចូលរូបភាពសម្រាប់ការផ្ទៀងផ្ទាត់ 1-to-1",
    "Select a clear, front-facing image (JPEG or PNG, max 16MB) to verify against the claimed user template.": "ជ្រើសរើសរូបភាពខាងមុខច្បាស់ (JPEG ឬ PNG, អតិបរមា 16MB) ដើម្បីផ្ទៀងផ្ទាត់ជាមួយទិន្នន័យគំរូ។",
    "Verify Uploaded Image": "ផ្ទៀងផ្ទាត់រូបភាពដែលបានបញ្ចូល",
    "Claimed user has no face enrolled": "អ្នកប្រើប្រាស់ដែលបានជ្រើសរើសមិនទាន់មានទម្រង់មុខទេ",
    "Multiple faces detected. 1 person only.": "បានរកឃើញមុខច្រើន។ សម្រាប់មនុស្ស 1 នាក់ប៉ុណ្ណោះ។",

    // Face Biometric Enrollment
    "Face Biometric Enrollment": "ការចុះឈ្មោះជីវមាត្រទម្រង់មុខ",
    "Informed Biometric Consent Notice": "សេចក្តីជូនដំណឹងអំពីការយល់ព្រមលើជីវមាត្រ",
    "I have read, understood, and voluntarily agree to the biometric enrollment policy.": "ខ្ញុំបានអាន យល់ច្បាស់ និងយល់ព្រមដោយស្ម័គ្រចិត្តចំពោះគោលការណ៍ចុះឈ្មោះជីវមាត្រ។",
    "Live Camera Feed": "ទិដ្ឋភាពកាមេរ៉ាផ្ទាល់",
    "Center face within the oval. Ensure even lighting.": "ដាក់មុខចំកណ្តាលរង្វង់ពងក្រពើ។ ធានាពន្លឺគ្រប់គ្រាន់។",
    "Capture & Enroll Face": "ថត និងចុះឈ្មោះទម្រង់មុខ",
    "Target Identity": "អត្តសញ្ញាណគោលដៅ",
    "Enrollment Quality Checks": "ការត្រួតពិនិត្យគុណភាពចុះឈ្មោះ",
    "Face Count:": "ចំនួនមុខ:",
    "Image Sharpness (Blur Metric):": "ភាពច្បាស់នៃរូបភាព:",
    "Illumination (Brightness):": "កម្រិតពន្លឺ:",
    "Requires ≥ 70.0 Laplacian variance.": "ត្រូវការ ≥ 70.0 Laplacian variance។",
    "Optimal range: 40 - 225 mean grayscale.": "កម្រិតល្អបំផុត: 40 - 225 mean grayscale។",
    "Must be exactly 1 face in camera frame.": "ត្រូវតែមានមុខតែ 1 គត់ក្នុងកាមេរ៉ា។",

    // Mood & Feeling Tracker
    "Live AI Face Mood & Affective Telemetry": "ការវាស់ស្ទង់អារម្មណ៍ទម្រង់មុខដោយ AI ផ្ទាល់",
    "AI Emotional & Wellness Telemetry": "ការវាស់ស្ទង់អារម្មណ៍ និងសុខុមាលភាពដោយ AI",
    "Auto-Capture Snapshot": "ថតរូបស្វ័យប្រវត្តិ",
    "Snapshot Mode:": "ទម្រង់ថតរូប:",
    "1 per unique person": "1ដង សម្រាប់មនុស្សម្នាក់",
    "Reset Captured Persons": "កំណត់អង្គចងចាំមនុស្សឡើងវិញ",
    "Log Manual Check-In": "កត់ត្រាវត្តមានផ្ទាល់",
    "Recent Emotion & Mood Check-Ins": "ការកត់ត្រាអារម្មណ៍ និងសុខុមាលភាពថ្មីៗ",
    "Awaiting Face...": "កំពុងរង់ចាំទម្រង់មុខ...",
    "Dominant Emotion": "អារម្មណ៍ចម្បង",
    "Valence (Pleasantness)": "កម្រិតរីករាយ (Valence)",
    "Arousal (Energy)": "កម្រិតថាមពល (Arousal)",
    "Emotion Breakdown": "ការបែងចែកអារម្មណ៍លម្អិត",
    "Recommended Wellness Action": "សកម្មភាពសុខុមាលភាពដែលបានណែនាំ",
    "Time": "ម៉ោង/ពេល",
    "Photo": "រូបថត",
    "Feeling / Mood": "អារម្មណ៍",
    "Confidence": "ទំនុកចិត្ត",
    "Valence": "កម្រិតរីករាយ",
    "Energy": "ថាមពល",
    "Context": "បរិបទ",
    "Note": "កំណត់ចំណាំ",

    // Attendance Kiosk & Logs
    "Live Attendance Kiosk": "កន្លែងកត់ត្រាវត្តមានផ្ទាល់",
    "Mark Attendance": "កត់ត្រាវត្តមាន",
    "Check In": "ចូលធ្វើការ",
    "Check Out": "ចេញពីធ្វើការ",
    "Employee": "បុគ្គលិក",
    "Timestamp": "ពេលវេលា",
    "Verification Method": "វិធីសាស្ត្រផ្ទៀងផ្ទាត់",
    "Facial Recognition": "ការសម្គាល់ទម្រង់មុខ",
    "PIN Verification": "ការផ្ទៀងផ្ទាត់ PIN",
    "Manual Override": "កត់ត្រាដោយដៃ",

    // Users Management
    "Add New User": "បន្ថែមអ្នកប្រើប្រាស់ថ្មី",
    "Edit User": "កែសម្រួលអ្នកប្រើប្រាស់",
    "Full Name": "ឈ្មោះពេញ",
    "Email": "អ៊ីមែល",
    "Biometric Status": "ស្ថានភាពជីវមាត្រ",
    "Active": "សកម្ម",
    "Inactive": "អសកម្ម",
    "Delete User": "លុបអ្នកប្រើប្រាស់",
    "Enroll Face": "ចុះឈ្មោះមុខ",
    "Re-enroll Face": "ចុះឈ្មោះមុខឡើងវិញ",

    // Profile & Common
    "Personal Information": "ព័ត៌មានផ្ទាល់ខ្លួន",
    "Change Password": "ប្តូរពាក្យសម្ងាត់",
    "Current Password": "ពាក្យសម្ងាត់បច្ចុប្បន្ន",
    "New Password": "ពាក្យសម្ងាត់ថ្មី",
    "Confirm New Password": "បញ្ជាក់ពាក្យសម្ងាត់ថ្មី",
    "Update Profile": "ធ្វើបច្ចុប្បន្នភាពគណនី",
    "Set Alternative PIN": "កំណត់លេខកូដ PIN ជំនួស",
    "Update PIN": "ធ្វើបច្ចុប្បន្នភាព PIN",
    "Alternative Non-Biometric PIN": "លេខកូដ PIN មិនមែនជីវមាត្រជំនួស",
    "PIN Active": "PIN សកម្ម",
    "Not Configured": "មិនទាន់កំណត់",
    "Configure a 4 to 6 digit numerical PIN to verify your identity and mark attendance whenever the camera is unavailable or if you choose not to use facial recognition.": "កំណត់លេខកូដ PIN ពី 4 ទៅ 6 ខ្ទង់ ដើម្បីផ្ទៀងផ្ទាត់អត្តសញ្ញាណ និងកត់ត្រាវត្តមាន នៅពេលកាមេរ៉ាមិនដំណើរការ ឬប្រសិនបើអ្នកមិនចង់ប្រើការសម្គាល់មុខ។",
    "Save": "រក្សាទុក",
    "Cancel": "បោះបង់",
    "Close": "បិទ",
    "Filter": "ចម្រោះ",
    "Export": "ទាញយកឯកសារ",
    "Success!": "ជោគជ័យ!",
    "Error": "កំហុស",
    "Warning": "ការព្រមាន",
    "Department": "នាយកដ្ឋាន",
    "Role": "តួនាទី",
    "Status": "ស្ថានភាព",
    "Actions": "សកម្មភាព",
    "Name": "ឈ្មោះ",
    "Date": "កាលបរិច្ឆេទ"
  }
};

// Current active language: "en" (English) or "km" (Khmer)
let currentLang = localStorage.getItem("frms_lang") || "en";
let isTranslating = false;

function initLanguage() {
  const saved = localStorage.getItem("frms_lang") || "en";
  setLanguage(saved, false);
}

function setLanguage(lang, persist = true) {
  if (lang !== "en" && lang !== "km") lang = "en";
  currentLang = lang;

  if (persist) {
    localStorage.setItem("frms_lang", lang);
    document.cookie = `frms_lang=${lang};path=/;max-age=31536000;SameSite=Lax`;
  }

  document.documentElement.setAttribute("data-lang", lang);
  document.documentElement.setAttribute("lang", lang);

  updateLanguageUI(lang);
  applyTranslations(lang);
}

function updateLanguageUI(lang) {
  const flag = lang === "km" ? "🇰🇭" : "🇬🇧";
  const label = lang === "km" ? "ខ្មែរ" : "EN";

  // Update topbar flag & labels
  document.querySelectorAll(".lang-flag-current").forEach(el => el.innerText = flag);
  document.querySelectorAll(".lang-label-current").forEach(el => el.innerText = label);

  const mainFlag = document.getElementById("langCurrentFlag");
  const mainLabel = document.getElementById("langCurrentLabel");
  if (mainFlag) mainFlag.innerText = flag;
  if (mainLabel) mainLabel.innerText = label;

  // Update checkmarks in dropdown menus
  document.querySelectorAll(".lang-check-en").forEach(el => {
    if (lang === "en") el.classList.remove("d-none");
    else el.classList.add("d-none");
  });
  document.querySelectorAll(".lang-check-km").forEach(el => {
    if (lang === "km") el.classList.remove("d-none");
    else el.classList.add("d-none");
  });

  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}

function applyTranslations(lang) {
  if (isTranslating) return;
  isTranslating = true;

  try {
    const dict = TRANSLATIONS[lang] || TRANSLATIONS.en;
    const enDict = TRANSLATIONS.en;

    // 1. Process elements with explicit data-i18n attribute
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        el.innerText = dict[key];
      }
    });

    // 2. Intelligent text-node replacement for common UI elements
    const selectors = [
      ".sidebar-nav-link span",
      ".nav-section-title",
      ".sidebar-footer span",
      "h1, h2, h3, h4, h5, h6",
      ".form-label",
      ".form-check-label",
      "button span",
      ".btn",
      ".badge",
      "th",
      ".dropdown-item span",
      ".dropdown-header",
      ".card-header-custom h6",
      ".camera-status-pill span",
      "#autoScannerText",
      "#resultHeading",
      "#resultMessage",
      "#enrolledStatusText",
      ".text-muted.small",
      ".brand-logo span"
    ];

    document.querySelectorAll(selectors.join(",")).forEach(el => {
      // Don't modify code elements, scripts, inputs, or dropdown menus with language options
      if (el.closest("#langSwitchBtn") || el.closest(".dropdown-menu")?.querySelector(".lang-check-en")) return;
      if (el.children.length > 2) return;

      // Save original English on first visit
      if (!el.hasAttribute("data-i18n-orig")) {
        const trimmed = el.innerText.trim();
        if (trimmed && enDict[trimmed]) {
          el.setAttribute("data-i18n-orig", trimmed);
        }
      }

      const origKey = el.getAttribute("data-i18n-orig");
      if (origKey) {
        if (lang === "km" && dict[origKey]) {
          if (el.children.length === 0) {
            el.innerText = dict[origKey];
          } else {
            for (let node of el.childNodes) {
              if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim() === origKey) {
                node.nodeValue = " " + dict[origKey] + " ";
                break;
              }
            }
          }
        } else if (lang === "en") {
          if (el.children.length === 0) {
            el.innerText = origKey;
          } else {
            for (let node of el.childNodes) {
              if (node.nodeType === Node.TEXT_NODE) {
                node.nodeValue = " " + origKey + " ";
                break;
              }
            }
          }
        }
      }
    });
  } catch (err) {
    console.warn("Translation apply error:", err);
  } finally {
    isTranslating = false;
  }
}

function t(key) {
  if (currentLang === "km" && TRANSLATIONS.km[key]) {
    return TRANSLATIONS.km[key];
  }
  return key;
}

// Auto-initialize on load and observe dynamic DOM updates
document.addEventListener("DOMContentLoaded", () => {
  initLanguage();

  const mainCont = document.querySelector(".app-main") || document.body;
  if (mainCont && window.MutationObserver) {
    const observer = new MutationObserver((mutations) => {
      if (isTranslating || currentLang !== "km") return;
      clearTimeout(window._transDebounce);
      window._transDebounce = setTimeout(() => {
        applyTranslations("km");
      }, 150);
    });
    observer.observe(mainCont, { childList: true, subtree: true });
  }
});

// Export globally
window.setLanguage = setLanguage;
window.initLanguage = initLanguage;
window.TRANSLATIONS = TRANSLATIONS;
window.t = t;
