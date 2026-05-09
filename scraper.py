#!/usr/bin/env python3
"""
Rose App Builder - Scraper Script
يبني هيكل تطبيق أندرويد كامل مع تشفير الملفات
"""

import os
import sys

def create_file(path, content):
    """إنشاء ملف مع المحتوى المحدد"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ تم إنشاء: {path}")

def build_project():
    """بناء هيكل المشروع بالكامل"""
    
    base = "app/src/main"
    java_base = f"{base}/java/com/rose/app"
    res_base = f"{base}/res"
    
    # ─── إعدادات Gradle ───
    create_file("settings.gradle", """\
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "RoseApp"
include ':app'
""")

    create_file("build.gradle", """\
plugins {
    id 'com.android.application' version '8.2.2' apply false
}
""")

    create_file("gradle.properties", """\
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
android.nonTransitiveRClass=true
""")

    create_file("gradle/wrapper/gradle-wrapper.properties", """\
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.5-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""")

    create_file("app/build.gradle", """\
plugins {
    id 'com.android.application'
}
android {
    namespace 'com.rose.app'
    compileSdk 34
    defaultConfig {
        applicationId "com.rose.app"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }
    buildTypes {
        release {
            minifyEnabled false
        }
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}
dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.recyclerview:recyclerview:1.3.1'
}
""")

    # ─── AndroidManifest ───
    create_file(f"{base}/AndroidManifest.xml", """\
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="Rose"
        android:theme="@style/Theme.Rose">
        <activity android:name=".LockScreenActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <activity android:name=".MainActivity" />
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.provider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/file_paths" />
        </provider>
    </application>
</manifest>
""")

    # ─── Java Classes ───
    create_file(f"{java_base}/LockScreenActivity.java", """\
package com.rose.app;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
public class LockScreenActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_lock_screen);
        EditText pinEditText = findViewById(R.id.pinEditText);
        Button unlockButton = findViewById(R.id.unlockButton);
        unlockButton.setOnClickListener(v -> {
            if (pinEditText.getText().toString().equals("1231")) {
                startActivity(new Intent(this, MainActivity.class));
                finish();
            } else {
                Toast.makeText(this, "رمز خاطئ", Toast.LENGTH_SHORT).show();
            }
        });
    }
}
""")

    create_file(f"{java_base}/FileItem.java", """\
package com.rose.app;
import java.util.Date;
public class FileItem {
    private final String displayName, filePath;
    private final Date date;
    public FileItem(String displayName, String filePath, Date date) {
        this.displayName = displayName;
        this.filePath = filePath;
        this.date = date;
    }
    public String getDisplayName() { return displayName; }
    public String getFilePath() { return filePath; }
    public Date getDate() { return date; }
}
""")

    create_file(f"{java_base}/CryptoUtils.java", """\
package com.rose.app;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.webkit.MimeTypeMap;
import androidx.core.content.FileProvider;
import java.io.*;
import java.security.SecureRandom;
import javax.crypto.*;
import javax.crypto.spec.*;
public class CryptoUtils {
    private static final String ALGORITHM = "AES/CBC/PKCS5Padding";
    public static void encryptFile(Context ctx, Uri inUri, File outFile, String key) throws Exception {
        SecretKeySpec sk = new SecretKeySpec(sha256(key), "AES");
        byte[] iv = new byte[16]; new SecureRandom().nextBytes(iv);
        Cipher c = Cipher.getInstance(ALGORITHM);
        c.init(Cipher.ENCRYPT_MODE, sk, new IvParameterSpec(iv));
        try (InputStream is = ctx.getContentResolver().openInputStream(inUri);
             OutputStream os = new FileOutputStream(outFile)) {
            os.write(iv);
            try (CipherOutputStream cos = new CipherOutputStream(os, c)) {
                byte[] buf = new byte[8192]; int len;
                while ((len = is.read(buf)) != -1) cos.write(buf, 0, len);
            }
        }
    }
    public static void decryptAndOpenFile(Context ctx, File encFile, String key) {
        try {
            File tmpDir = new File(ctx.getCacheDir(), "temp_decrypted"); tmpDir.mkdirs();
            File decFile = new File(tmpDir, encFile.getName().replaceFirst("ENC_\\\\d+_", ""));
            SecretKeySpec sk = new SecretKeySpec(sha256(key), "AES");
            try (FileInputStream fis = new FileInputStream(encFile)) {
                byte[] iv = new byte[16]; fis.read(iv);
                Cipher c = Cipher.getInstance(ALGORITHM);
                c.init(Cipher.DECRYPT_MODE, sk, new IvParameterSpec(iv));
                try (CipherInputStream cis = new CipherInputStream(fis, c);
                     FileOutputStream fos = new FileOutputStream(decFile)) {
                    byte[] buf = new byte[8192]; int len;
                    while ((len = cis.read(buf)) != -1) fos.write(buf, 0, len);
                }
            }
            Uri uri = FileProvider.getUriForFile(ctx, ctx.getPackageName() + ".provider", decFile);
            String mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(MimeTypeMap.getFileExtensionFromUrl(decFile.getName()));
            Intent i = new Intent(Intent.ACTION_VIEW).setDataAndType(uri, mime);
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            ctx.startActivity(i);
        } catch (Exception ignored) {}
    }
    public static String getFileName(Context ctx, Uri uri) {
        String n = "unknown";
        try (android.database.Cursor c = ctx.getContentResolver().query(uri, null, null, null, null)) {
            if (c != null && c.moveToFirst()) {
                int i = c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME);
                if (i >= 0) n = c.getString(i);
            }
        } catch (Exception ignored) {}
        return n;
    }
    private static byte[] sha256(String s) throws Exception {
        return java.security.MessageDigest.getInstance("SHA-256").digest(s.getBytes("UTF-8"));
    }
}
""")

    create_file(f"{java_base}/MainActivity.java", """\
package com.rose.app;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import java.io.File;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
public class MainActivity extends AppCompatActivity {
    private RecyclerView chatRecyclerView;
    private ChatAdapter adapter;
    private List<FileItem> fileItemList = new ArrayList<>();
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        chatRecyclerView = findViewById(R.id.chatRecyclerView);
        chatRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        adapter = new ChatAdapter();
        chatRecyclerView.setAdapter(adapter);
        findViewById(R.id.addImageButton).setOnClickListener(v -> openFilePicker("image/*"));
        findViewById(R.id.addVideoButton).setOnClickListener(v -> openFilePicker("video/*"));
        findViewById(R.id.addFileButton).setOnClickListener(v -> openFilePicker("*/*"));
        loadExistingFiles();
    }
    private void openFilePicker(String mimeType) {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.setType(mimeType);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(Intent.createChooser(intent, "اختر ملف"), 100);
    }
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 100 && resultCode == RESULT_OK && data != null && data.getData() != null) {
            encryptAndSaveFile(data.getData());
        }
    }
    private void encryptAndSaveFile(Uri uri) {
        try {
            File encryptedDir = new File(getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS), "Rose_Encrypted");
            if (!encryptedDir.exists()) encryptedDir.mkdirs();
            String originalName = CryptoUtils.getFileName(this, uri);
            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
            File encryptedFile = new File(encryptedDir, "ENC_" + timestamp + "_" + originalName);
            CryptoUtils.encryptFile(this, uri, encryptedFile, "MySecretKey12345");
            fileItemList.add(0, new FileItem(originalName, encryptedFile.getAbsolutePath(), new Date()));
            adapter.notifyItemInserted(0);
            chatRecyclerView.scrollToPosition(0);
            Toast.makeText(this, "تم التشفير ✓", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, "فشل: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }
    private void loadExistingFiles() {
        File encryptedDir = new File(getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS), "Rose_Encrypted");
        if (encryptedDir.exists()) {
            File[] files = encryptedDir.listFiles();
            if (files != null) for (File file : files) {
                fileItemList.add(new FileItem(
                    file.getName().replaceFirst("ENC_\\\\d+_", ""),
                    file.getAbsolutePath(),
                    new Date(file.lastModified())
                ));
            }
        }
        adapter.notifyDataSetChanged();
    }
    class ChatAdapter extends RecyclerView.Adapter<ChatAdapter.VH> {
        @NonNull @Override
        public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new VH(LayoutInflater.from(parent.getContext()).inflate(R.layout.chat_item, parent, false));
        }
        @Override
        public void onBindViewHolder(@NonNull VH h, int pos) {
            FileItem item = fileItemList.get(pos);
            h.name.setText(item.getDisplayName());
            h.date.setText(new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(item.getDate()));
            String n = item.getDisplayName().toLowerCase();
            if (n.matches(".*\\\\.(jpg|jpeg|png|gif)$")) h.icon.setImageResource(android.R.drawable.ic_menu_gallery);
            else if (n.matches(".*\\\\.(mp4|avi|mkv|mov)$")) h.icon.setImageResource(android.R.drawable.ic_media_play);
            else h.icon.setImageResource(android.R.drawable.ic_menu_save);
            h.itemView.setOnClickListener(v -> CryptoUtils.decryptAndOpenFile(MainActivity.this, new File(item.getFilePath()), "MySecretKey12345"));
        }
        @Override public int getItemCount() { return fileItemList.size(); }
        class VH extends RecyclerView.ViewHolder {
            ImageView icon; TextView name, date;
            VH(View v) { super(v); icon = v.findViewById(R.id.typeIcon); name = v.findViewById(R.id.fileNameText); date = v.findViewById(R.id.dateText); }
        }
    }
}
""")

    # ─── XML Layouts ───
    create_file(f"{res_base}/layout/activity_lock_screen.xml", """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:gravity="center" android:orientation="vertical" android:background="#1C1C1E">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="🌹" android:textSize="64sp" />
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_marginTop="8dp" android:text="Rose" android:textColor="#FFFFFF"
        android:textSize="32sp" android:textStyle="bold" />
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:layout_marginTop="4dp" android:text="الذاكرة المشفرة" android:textColor="#8E8E93"
        android:textSize="14sp" />
    <EditText android:id="@+id/pinEditText" android:layout_width="200dp"
        android:layout_height="wrap_content" android:layout_marginTop="40dp"
        android:inputType="numberPassword" android:textColor="#FFFFFF" android:textColorHint="#757575"
        android:hint="أدخل رمز PIN" android:maxLength="4" android:textSize="18sp"
        android:gravity="center" android:backgroundTint="#007AFF" />
    <Button android:id="@+id/unlockButton" android:layout_width="200dp"
        android:layout_height="48dp" android:layout_marginTop="20dp" android:text="فتح"
        android:backgroundTint="#007AFF" android:textColor="#FFFFFF" android:textSize="16sp" />
</LinearLayout>
""")

    create_file(f"{res_base}/layout/activity_main.xml", """\
<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#000000">
    <LinearLayout android:id="@+id/toolbar" android:layout_width="match_parent"
        android:layout_height="56dp" android:background="#1C1C1E"
        android:gravity="center_vertical" android:paddingHorizontal="16dp" android:elevation="4dp">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="💬 Rose" android:textColor="#FFFFFF"
            android:textSize="18sp" android:textStyle="bold"/>
    </LinearLayout>
    <androidx.recyclerview.widget.RecyclerView android:id="@+id/chatRecyclerView"
        android:layout_width="match_parent" android:layout_height="match_parent"
        android:layout_below="@id/toolbar" android:layout_above="@id/bottomBar"
        android:padding="8dp" android:clipToPadding="false"/>
    <LinearLayout android:id="@+id/bottomBar" android:layout_width="match_parent"
        android:layout_height="64dp" android:layout_alignParentBottom="true"
        android:background="#1C1C1E" android:gravity="center" android:orientation="horizontal"
        android:paddingHorizontal="16dp" android:elevation="8dp">
        <Button android:id="@+id/addImageButton" android:layout_width="0dp"
            android:layout_height="44dp" android:layout_weight="1" android:layout_marginEnd="6dp"
            android:text="📷 صورة" android:textSize="13sp" android:backgroundTint="#007AFF" android:textColor="#FFFFFF"/>
        <Button android:id="@+id/addVideoButton" android:layout_width="0dp"
            android:layout_height="44dp" android:layout_weight="1" android:layout_marginHorizontal="3dp"
            android:text="🎬 فيديو" android:textSize="13sp" android:backgroundTint="#34C759" android:textColor="#FFFFFF"/>
        <Button android:id="@+id/addFileButton" android:layout_width="0dp"
            android:layout_height="44dp" android:layout_weight="1" android:layout_marginStart="6dp"
            android:text="📁 ملف" android:textSize="13sp" android:backgroundTint="#FF9500" android:textColor="#FFFFFF"/>
    </LinearLayout>
</RelativeLayout>
""")

    create_file(f"{res_base}/layout/chat_item.xml", """\
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="wrap_content"
    android:orientation="vertical" android:background="#1C1C1E"
    android:padding="14dp" android:layout_marginBottom="2dp"
    android:clickable="true" android:focusable="true"
    android:foreground="?attr/selectableItemBackground">
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:gravity="center_vertical">
        <ImageView android:id="@+id/typeIcon" android:layout_width="32dp"
            android:layout_height="32dp" android:src="@android:drawable/ic_menu_gallery" />
        <TextView android:id="@+id/fileNameText" android:layout_width="0dp"
            android:layout_height="wrap_content" android:layout_weight="1"
            android:layout_marginStart="12dp" android:text="filename.jpg"
            android:textColor="#FFFFFF" android:textSize="15sp"
            android:maxLines="1" android:ellipsize="middle" />
        <ImageView android:layout_width="20dp" android:layout_height="20dp"
            android:src="@android:drawable/ic_menu_view" android:alpha="0.5" />
    </LinearLayout>
    <TextView android:id="@+id/dateText" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:layout_marginStart="44dp"
        android:layout_marginTop="4dp" android:text="2026-05-09 19:30"
        android:textColor="#8E8E93" android:textSize="12sp" />
</LinearLayout>
""")

    # ─── Resource files ───
    create_file(f"{res_base}/xml/file_paths.xml", """\
<?xml version="1.0" encoding="utf-8"?>
<paths>
    <cache-path name="decrypted_files" path="temp_decrypted/" />
</paths>
""")

    create_file(f"{res_base}/values/colors.xml", """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="black">#FF000000</color>
    <color name="dark_gray">#FF1C1C1E</color>
    <color name="white">#FFFFFFFF</color>
    <color name="blue">#FF007AFF</color>
    <color name="green">#FF34C759</color>
    <color name="orange">#FFFF9500</color>
    <color name="light_gray">#FF8E8E93</color>
</resources>
""")

    create_file(f"{res_base}/values/strings.xml", """\
<resources>
    <string name="app_name">Rose</string>
</resources>
""")

    create_file(f"{res_base}/values/themes.xml", """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.Rose" parent="Theme.AppCompat.Light.NoActionBar">
        <item name="colorPrimary">#FF007AFF</item>
        <item name="colorPrimaryDark">#FF000000</item>
        <item name="colorAccent">#FF007AFF</item>
        <item name="android:statusBarColor">#FF1C1C1E</item>
        <item name="android:navigationBarColor">#FF1C1C1E</item>
        <item name="android:windowBackground">#FF000000</item>
    </style>
</resources>
""")

    print("\n✅ تم بناء جميع ملفات المشروع بنجاح!")
    print("📁 جاهز للبناء في GitHub Actions\n")

if __name__ == "__main__":
    build_project()
