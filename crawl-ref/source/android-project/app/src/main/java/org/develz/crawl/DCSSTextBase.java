package org.develz.crawl;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.widget.EditText;
import android.widget.TextView;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;

public abstract class DCSSTextBase extends AppCompatActivity {

    private static final int CREATE_FILE = 1;

    private TextView textToDownload;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
    }

    // Load the file
    protected boolean openFile(File file, TextView text) {
        try {
            Log.i(DCSSLauncher.TAG, "Opening file: " + file.getAbsolutePath());
            text.setText(readUtf8(new FileInputStream(file)));
            return true;
        } catch (IOException e) {
            Log.e(DCSSLauncher.TAG, "Can't open file: " + e.getMessage());
            return false;
        }
    }

    // Read through EOF, including streams whose reads return only part of the
    // requested data. The reader owns and closes the supplied stream.
    static String readUtf8(InputStream input) throws IOException {
        try (Reader reader = new InputStreamReader(input, StandardCharsets.UTF_8.newDecoder())) {
            StringBuilder text = new StringBuilder();
            char[] buffer = new char[4096];
            int length;
            while ((length = reader.read(buffer)) != -1) {
                text.append(buffer, 0, length);
            }
            return text.toString();
        }
    }

    // Android uses an atomic rename when both files are on the same filesystem.
    // Never truncate or remove the original before the replacement is ready.
    static void writeUtf8(File file, CharSequence text) throws IOException {
        File target = file.getAbsoluteFile();
        File temporary = File.createTempFile(".dcss-" + target.getName(), ".tmp",
                target.getParentFile());
        try {
            try (FileOutputStream output = new FileOutputStream(temporary);
                    Writer writer = new OutputStreamWriter(output,
                            StandardCharsets.UTF_8.newEncoder())) {
                writer.append(text);
                writer.flush();
                output.getFD().sync();
            }
            if (!temporary.renameTo(target)) {
                throw new IOException("Can't replace file: " + target);
            }
        } finally {
            temporary.delete();
        }
    }

    // Save the file, leaving both the original file and editor intact on failure.
    protected boolean saveFile(File file, EditText text) {
        try {
            Log.i(DCSSLauncher.TAG, "Saving file: " + file.getAbsolutePath());
            writeUtf8(file, text.getText());
            return true;
        } catch (IOException e) {
            Log.e(DCSSLauncher.TAG, "Can't save file: " + e.getMessage());
            return false;
        }
    }

    // Load the asset
    protected boolean openAsset(String asset, TextView text) {
        try {
            Log.i(DCSSLauncher.TAG, "Opening asset: " + asset);
            text.setText(readUtf8(getAssets().open(asset)));
            return true;
        } catch (IOException e) {
            Log.e(DCSSLauncher.TAG, "Can't open asset: " + e.getMessage());
            return false;
        }
    }

    // Download the file
    // Actually show a file picker to save the file
    protected void downloadFile(TextView text, String fileName) {
        Log.i(DCSSLauncher.TAG, "Downloading file: " + fileName);
        textToDownload = text;
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("text/plain");
        intent.putExtra(Intent.EXTRA_TITLE, fileName);
        downloadActivityResultLauncher.launch(intent);
    }

    // Handling the download
    // Save the file in the destination chosen by the user
    ActivityResultLauncher<Intent> downloadActivityResultLauncher = registerForActivityResult(
        new ActivityResultContracts.StartActivityForResult(),
        result -> {
            if (result.getResultCode() == Activity.RESULT_OK) {
                // There are no request codes
                Intent resultData = result.getData();
                if (resultData != null && resultData.getData() != null) {
                    try {
                        Uri uri = resultData.getData();
                        Log.i(DCSSLauncher.TAG, "Destination: " + uri.toString());
                        OutputStream outputStream = getContentResolver().openOutputStream(uri);
                        OutputStreamWriter writer = new OutputStreamWriter(outputStream);
                        writer.append(textToDownload.getText());
                        writer.close();
                        onDownloadOk();
                    } catch (IOException e) {
                        Log.e(DCSSLauncher.TAG, "Can't download file: " + e.getMessage());
                        onDownloadError();
                    }
                }
            }
        });

    // Overridden by children to show download results
    protected abstract void onDownloadOk();
    protected abstract void onDownloadError();

    // Close the activity without saving
    protected void close() {
        finish();
    }

}
