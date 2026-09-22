package org.develz.crawl;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;

import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AlertDialog;

import java.io.File;
import java.util.Locale;

public class DCSSTextEditor extends DCSSTextBase {

    private static final String OPTIONS_GUIDE = "docs/options_guide.txt";
    private static final String ZH_OPTIONS_GUIDE = "docs/zh/options_guide.txt";
    private static final String STATE_ORIGINAL_TEXT = "original_text";
    private static final String STATE_EDITOR_TEXT = "editor_text";
    private static final String STATE_FILE_OPENED = "file_opened";
    private static final String STATE_STATUS = "status";
    private static final String STATE_SELECTION_START = "selection_start";
    private static final String STATE_SELECTION_END = "selection_end";

    static String optionsGuideAsset(Locale locale) {
        return locale != null && "zh".equals(locale.getLanguage())
                ? ZH_OPTIONS_GUIDE : OPTIONS_GUIDE;
    }

    private File file;

    private EditText editor;

    private TextView status;
    private String originalText;
    private boolean fileOpened;
    private AlertDialog discardDialog;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.text_editor);

        Intent intent = getIntent();
        file = (File) intent.getSerializableExtra("file");

        editor = findViewById(R.id.textEditor);
        // Save the text together with its original baseline below, so restoring
        // this Activity never reloads over unsaved edits or resets dirty state.
        editor.setSaveEnabled(false);
        status = findViewById(R.id.status);

        findViewById(R.id.saveButton).setOnClickListener(this::onClickSave);
        findViewById(R.id.cancelButton).setOnClickListener(this::onClickClose);
        findViewById(R.id.helpButton).setOnClickListener(this::onClickHelp);

        if (savedInstanceState == null) {
            fileOpened = openFile(file, editor);
            originalText = editor.getText().toString();
            if (!fileOpened) {
                status.setText(R.string.open_error);
            }
        } else {
            originalText = savedInstanceState.getString(STATE_ORIGINAL_TEXT, "");
            editor.setText(savedInstanceState.getString(STATE_EDITOR_TEXT, originalText));
            fileOpened = savedInstanceState.getBoolean(STATE_FILE_OPENED);
            status.setText(savedInstanceState.getCharSequence(STATE_STATUS));
            int length = editor.length();
            int start = savedInstanceState.getInt(STATE_SELECTION_START, length);
            int end = savedInstanceState.getInt(STATE_SELECTION_END, length);
            editor.setSelection(Math.max(0, Math.min(start, length)),
                    Math.max(0, Math.min(end, length)));
        }
        // Do not overwrite a file whose original contents could not be read.
        findViewById(R.id.saveButton).setEnabled(fileOpened);

        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                requestClose();
            }
        });
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        outState.putString(STATE_ORIGINAL_TEXT, originalText);
        outState.putString(STATE_EDITOR_TEXT, editor.getText().toString());
        outState.putBoolean(STATE_FILE_OPENED, fileOpened);
        outState.putCharSequence(STATE_STATUS, status.getText());
        outState.putInt(STATE_SELECTION_START, editor.getSelectionStart());
        outState.putInt(STATE_SELECTION_END, editor.getSelectionEnd());
        super.onSaveInstanceState(outState);
    }

    @Override
    protected void onDestroy() {
        if (discardDialog != null) {
            discardDialog.dismiss();
        }
        super.onDestroy();
    }

    // Save button
    private void onClickSave(View v) {
        status.setText("");
        if (saveFile(file, editor)) {
            close();
        } else {
            status.setText(R.string.save_error);
        }
    }

    // Close button
    private void onClickClose(View v) {
        requestClose();
    }

    private void requestClose() {
        if (originalText.contentEquals(editor.getText())) {
            close();
        } else if (discardDialog == null) {
            discardDialog = new AlertDialog.Builder(this)
                    .setTitle(R.string.discard_changes_title)
                    .setMessage(R.string.discard_changes_message)
                    .setNegativeButton(R.string.keep_editing, (dialog, which) -> {})
                    .setPositiveButton(R.string.discard_changes, (dialog, which) -> close())
                    .create();
            discardDialog.setOnDismissListener(dialog -> discardDialog = null);
            discardDialog.show();
        }
    }

    // Help button
    private void onClickHelp(View v) {
        status.setText("");
        Intent intent = new Intent(getBaseContext(), DCSSTextViewer.class);
        intent.putExtra("asset", optionsGuideAsset(Locale.getDefault()));
        startActivity(intent);
    }

    @Override
    protected void onDownloadOk() {}

    @Override
    protected void onDownloadError() {}

}
