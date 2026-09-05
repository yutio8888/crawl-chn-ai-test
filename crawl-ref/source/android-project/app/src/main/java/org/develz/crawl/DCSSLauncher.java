package org.develz.crawl;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CompoundButton;
import android.widget.EditText;
import android.widget.Spinner;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Locale;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.SwitchCompat;

public class DCSSLauncher extends AppCompatActivity implements AdapterView.OnItemSelectedListener, CompoundButton.OnCheckedChangeListener {

    public final static String TAG = "LAUNCHER";

    private static final String INIT_FILE = "init.txt";

    // Crawl's init file
    private File initFile;

    // Android options
    private SharedPreferences preferences;

    // Current keyboard type
    private int keyboardOption;

    // Extra keyboard options
    private int extraKeyboardOption;

    // Keyboard size input
    EditText ksizeEditText;

    // Keyboard size in pixels
    private float keyboardSizePx;

    // Default keyboard size in dp
    private int defaultKbSizeDp;

    // Screen density
    private float density;

    // Full screen input
    SwitchCompat fullScreenSwitch;

    // Full screen
    private boolean fullScreen;

    @Override
    protected void onCreate(Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);

        Log.i("AndroidStartup", "launcher_on_create elapsed_realtime_ms="
                + SystemClock.elapsedRealtime());
        setContentView(R.layout.launcher);

        findViewById(R.id.startButton).setOnClickListener(this::startGame);
        findViewById(R.id.editInitFile).setOnClickListener(this::editInitFile);
        findViewById(R.id.morgueButton).setOnClickListener(this::openMorgue);
        findViewById(R.id.modsButton).setOnClickListener(this::openMods);

        boolean isPC = getPackageManager().hasSystemFeature(PackageManager.FEATURE_PC);
        boolean isTV = getPackageManager().hasSystemFeature(PackageManager.FEATURE_LEANBACK);
        int defaultKeyboard = 4;
        int defaultExtraKeyboard = 0;
        if (isPC || isTV) {
            defaultKeyboard = 0;
            defaultExtraKeyboard = 0;
        }

        preferences = getPreferences(Context.MODE_PRIVATE);
        keyboardOption = preferences.getInt("keyboard", defaultKeyboard);
        extraKeyboardOption = preferences.getInt("extra_keyboard", defaultExtraKeyboard);
        fullScreen = preferences.getBoolean("full_screen", true);

        // Density is the relationship between px and dp
        density = getResources().getDisplayMetrics().density;
        defaultKbSizeDp = Math.round(getResources().getDimension(R.dimen.key_height) / density);
        int storedKeyboardSizeDp = preferences.getInt("keyboard_size", defaultKbSizeDp);
        int keyboardSizeDp = normalizedKeyboardSize(Integer.toString(storedKeyboardSizeDp));
        if (keyboardSizeDp != storedKeyboardSizeDp) {
            preferences.edit().putInt("keyboard_size", keyboardSizeDp).apply();
        }
        keyboardSizePx = keyboardSizeDp * density;

        // Keyboard spinner
        Spinner keyboardSpinner = findViewById(R.id.keyboardSpinner);
        ArrayAdapter<CharSequence> arrayAdapter = ArrayAdapter.createFromResource(
                this, R.array.keyboard_options, android.R.layout.simple_spinner_item);
        arrayAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        keyboardSpinner.setAdapter(arrayAdapter);
        keyboardSpinner.setOnItemSelectedListener(this);
        keyboardSpinner.setSelection(keyboardOption);

        // Extra keyboard spinner
        Spinner extraKeyboardSpinner = findViewById(R.id.extraKeyboardSpinner);
        ArrayAdapter<CharSequence> extraArrayAdapter = ArrayAdapter.createFromResource(
                this, R.array.extra_keyboard_options, android.R.layout.simple_spinner_item);
        extraArrayAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        extraKeyboardSpinner.setAdapter(extraArrayAdapter);
        extraKeyboardSpinner.setOnItemSelectedListener(this);
        extraKeyboardSpinner.setSelection(extraKeyboardOption);

        // Keyboard size input
        ksizeEditText = findViewById(R.id.keyboardSize);
        ksizeEditText.setText(String.format(Locale.getDefault(), "%d", keyboardSizeDp));
        ksizeEditText.setOnFocusChangeListener((view, hasFocus) -> {
            if (!hasFocus) {
                commitKeyboardSize();
            }
        });
        ksizeEditText.setOnEditorActionListener((view, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_DONE) {
                commitKeyboardSize();
            }
            // Let the IME also perform its normal Done action (dismissal).
            return false;
        });

        // Full screen switch
        fullScreenSwitch = findViewById(R.id.fullScreen);
        fullScreenSwitch.setChecked(fullScreen);
        fullScreenSwitch.setOnCheckedChangeListener(this);

        setupExpandableGroup(R.id.inputDisplayButton, R.id.inputDisplayGroup,
                R.string.input_display);
        setupExpandableGroup(R.id.advancedButton, R.id.advancedGroup,
                R.string.advanced);

        // Native mkdir cannot traverse Android's scoped-storage ancestors, so
        // create the writable directory layout through the Android API first.
        File externalFilesDir = getExternalFilesDir(null);
        if (externalFilesDir == null) {
            Log.e(TAG, "External files directory is unavailable");
            findViewById(R.id.startButton).setEnabled(false);
            findViewById(R.id.editInitFile).setEnabled(false);
            findViewById(R.id.morgueButton).setEnabled(false);
            findViewById(R.id.modsButton).setEnabled(false);
            return;
        }
        String versionName = null;
        try {
            versionName = getPackageManager()
                    .getPackageInfo(getPackageName(), 0).versionName;
        } catch (PackageManager.NameNotFoundException e) {
            Log.e(TAG, "Can't read package version", e);
        }
        if (versionName == null
                || !createGameDirectories(externalFilesDir, versionName)) {
            Log.e(TAG, "Can't create game directories");
            findViewById(R.id.startButton).setEnabled(false);
        }

        // Create the init file if needed
        initFile = new File(externalFilesDir, INIT_FILE);
        resetInitFile(false);

        // TV users get a warning
        if (isTV) {
            boolean shown = preferences.getBoolean("tv_warning_shown", false);
            if (!shown) {
                AlertDialog.Builder builder = new AlertDialog.Builder(DCSSLauncher.this);
                builder.setMessage(R.string.tv_warning);
                builder.setCancelable(false);
                builder.setNegativeButton(R.string.ok, (dialog, which) -> {
                    dialog.cancel();
                });
                builder.create().show();
                preferences.edit().putBoolean("tv_warning_shown", true).apply();
            }
        }
    }

    private void setupExpandableGroup(int buttonId, int groupId, int labelId) {
        Button button = findViewById(buttonId);
        View group = findViewById(groupId);
        String label = getString(labelId);
        button.setText("+ " + label);
        button.setContentDescription(label);
        button.setOnClickListener(view -> {
            boolean expand = group.getVisibility() != View.VISIBLE;
            // A touch-focusable Button consumes its first tap just to focus.
            // Keep touch focus on the container instead, also committing any
            // size edit and preventing expansion from opening the IME.
            if (button.isInTouchMode()) {
                findViewById(R.id.launcherRoot).requestFocus();
            }
            if (!expand) {
                // Focus loss commits the size edit before hiding its controls.
                if (!button.isInTouchMode()) {
                    button.requestFocus();
                }
                InputMethodManager ime = (InputMethodManager)
                        getSystemService(Context.INPUT_METHOD_SERVICE);
                if (ime != null) {
                    ime.hideSoftInputFromWindow(button.getWindowToken(), 0);
                }
            }
            group.setVisibility(expand ? View.VISIBLE : View.GONE);
            button.setText((expand ? "− " : "+ ") + label);
        });
        button.setAccessibilityDelegate(new View.AccessibilityDelegate() {
            @Override
            public void onInitializeAccessibilityNodeInfo(View host,
                                                         AccessibilityNodeInfo info) {
                super.onInitializeAccessibilityNodeInfo(host, info);
                info.addAction(group.getVisibility() == View.VISIBLE
                        ? AccessibilityNodeInfo.AccessibilityAction.ACTION_COLLAPSE
                        : AccessibilityNodeInfo.AccessibilityAction.ACTION_EXPAND);
            }

            @Override
            public boolean performAccessibilityAction(View host, int action,
                                                      Bundle arguments) {
                int expected = group.getVisibility() == View.VISIBLE
                        ? AccessibilityNodeInfo.ACTION_COLLAPSE
                        : AccessibilityNodeInfo.ACTION_EXPAND;
                if (action == expected) {
                    return host.performClick();
                }
                return super.performAccessibilityAction(host, action, arguments);
            }
        });
    }

    static boolean createGameDirectories(File externalFilesDir, String version) {
        if (externalFilesDir == null) {
            return false;
        }

        String[] directories = {
            "saves",
            "morgue",
            "saves/bones",
            "saves/sprint",
            "saves/sprint/bones",
            "saves/descent",
            "saves/descent/bones",
            "saves/cache." + version + "/db",
            "saves/cache." + version + "/des"
        };
        for (String directory : directories) {
            File path = new File(externalFilesDir, directory);
            if (!path.isDirectory() && !path.mkdirs() && !path.isDirectory()) {
                // Another caller may have created the directory after the
                // first check. Only fail if it is still missing.
                return false;
            }
        }
        return true;
    }

    // Start game
    private void startGame(View v) {
        // A touch on Start need not move focus away from the size editor.
        commitKeyboardSize();
        long clickTime = SystemClock.elapsedRealtime();
        Log.i("AndroidStartup", "start_game_click elapsed_realtime_ms=" + clickTime);
        Intent intent = new Intent(getBaseContext(), DungeonCrawlStoneSoup.class);
        intent.putExtra("startup_click_ms", clickTime);
        intent.putExtra("keyboard", keyboardOption);
        intent.putExtra("extra_keyboard", extraKeyboardOption);
        intent.putExtra("keyboard_size", Math.round(keyboardSizePx));
        intent.putExtra("full_screen", fullScreen);
        startActivity(intent);
    }

    // Reset the init file
    private void resetInitFile(boolean force) {
        if (!initFile.exists() || force) {
            try {
                FileWriter writer = new FileWriter(initFile);
                writer.close();
            } catch (IOException e) {
                Log.e(TAG, "Can't write init file: " + e.getMessage());
            }
        }
    }

    // Edit init file
    private void editInitFile(View v) {
        Intent intent = new Intent(getBaseContext(), DCSSTextEditor.class);
        intent.putExtra("file", initFile);
        startActivity(intent);
    }

    // Open morgue
    private void openMorgue(View v) {
        Intent intent = new Intent(getBaseContext(), DCSSMorgue.class);
        startActivity(intent);
    }

    // Open mods
    private void openMods(View v) {
        Intent intent = new Intent(getBaseContext(), DCSSMods.class);
        startActivity(intent);
    }

    // Keyboard changed
    @Override
    public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
        if (parent.getId() == R.id.keyboardSpinner) {
            keyboardOption = position;
            preferences.edit().putInt("keyboard", position).apply();
            if (ksizeEditText != null) {
                commitKeyboardSize();
            }
        } else if (parent.getId() == R.id.extraKeyboardSpinner) {
            extraKeyboardOption = position;
            preferences.edit().putInt("extra_keyboard", position).apply();
        }
    }

    @Override
    public void onNothingSelected(AdapterView<?> parent) {
        // This shouldn't happen
    }

    private void commitKeyboardSize() {
        int keyboardSizeDp = normalizedKeyboardSize(ksizeEditText.getText().toString());
        String normalized = String.format(Locale.getDefault(), "%d", keyboardSizeDp);
        if (!normalized.contentEquals(ksizeEditText.getText())) {
            ksizeEditText.setText(normalized);
            ksizeEditText.setSelection(normalized.length());
        }
        keyboardSizePx = keyboardSizeDp * density;
        preferences.edit().putInt("keyboard_size", keyboardSizeDp).apply();
    }

    private int normalizedKeyboardSize(String input) {
        // The full keyboard has four rows. Limit a key row to one sixth of the
        // shortest display side so rotation always leaves room for the game
        // surface, including row spacing and system insets.
        int shortestSidePx = Math.min(
                getResources().getDisplayMetrics().widthPixels,
                getResources().getDisplayMetrics().heightPixels);
        return normalizeKeyboardSizeDp(input, keyboardOption, defaultKbSizeDp,
                (int) Math.floor(shortestSidePx / density / 6.0f));
    }

    static int normalizeKeyboardSizeDp(String input, int keyboardOption,
                                       int defaultSizeDp, int displayLimitDp) {
        int requestedSizeDp;
        try {
            requestedSizeDp = Integer.parseInt(input);
        } catch (NumberFormatException e) {
            requestedSizeDp = defaultSizeDp;
        }
        // Match the compact keyboard's actual touch target. Other modes keep
        // accepting zero, and keyboard visibility remains controlled by mode.
        int minimumSizeDp = keyboardOption == 4 ? DCSSKeyboard.MINIMUM_TOUCH_TARGET_DP : 0;
        int maximumSizeDp = Math.max(minimumSizeDp, Math.max(defaultSizeDp, displayLimitDp));
        return Math.max(minimumSizeDp, Math.min(requestedSizeDp, maximumSizeDp));
    }

    @Override
    public void onCheckedChanged(CompoundButton compoundButton, boolean b) {
        fullScreen = b;
        preferences.edit().putBoolean("full_screen", fullScreen).apply();
    }

}
