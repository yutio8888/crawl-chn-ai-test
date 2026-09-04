package org.develz.crawl;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.os.Bundle;
import android.os.SystemClock;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
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

public class DCSSLauncher extends AppCompatActivity implements AdapterView.OnItemSelectedListener, TextWatcher, CompoundButton.OnCheckedChangeListener {

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

    // Guard TextWatcher callbacks while normalizing an out-of-range value.
    private boolean updatingKeyboardSize;

    // Screen density
    private float density;

    // Full screen input
    SwitchCompat fullScreenSwitch;

    // Full screen
    private boolean fullScreen;

    @Override
    protected void onCreate(Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);

        Configuration configuration = new Configuration(
                getResources().getConfiguration());
        configuration.setLocale(Locale.SIMPLIFIED_CHINESE);
        getResources().updateConfiguration(
                configuration, getResources().getDisplayMetrics());

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
        int keyboardSizeDp = clampKeyboardSizeDp(storedKeyboardSizeDp);
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
        ksizeEditText.addTextChangedListener(this);

        // Full screen switch
        fullScreenSwitch = findViewById(R.id.fullScreen);
        fullScreenSwitch.setChecked(fullScreen);
        fullScreenSwitch.setOnCheckedChangeListener(this);

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
                // Locale-aware activity creation can overlap a configuration
                // restart. Treat a directory won by the other instance as
                // success rather than disabling Start Game.
                return false;
            }
        }
        return true;
    }

    // Start game
    private void startGame(View v) {
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
        } else if (parent.getId() == R.id.extraKeyboardSpinner) {
            extraKeyboardOption = position;
            preferences.edit().putInt("extra_keyboard", position).apply();
        }
    }

    @Override
    public void onNothingSelected(AdapterView<?> parent) {
        // This shouldn't happen
    }

    @Override
    public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {}

    @Override
    public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {
        if (updatingKeyboardSize) {
            return;
        }
        try {
            int requestedSizeDp = Integer.parseInt(charSequence.toString());
            int keyboardSizeDp = clampKeyboardSizeDp(requestedSizeDp);
            if (keyboardSizeDp != requestedSizeDp) {
                updatingKeyboardSize = true;
                ksizeEditText.setText(String.format(Locale.getDefault(), "%d", keyboardSizeDp));
                ksizeEditText.setSelection(ksizeEditText.getText().length());
                updatingKeyboardSize = false;
            }
            keyboardSizePx = keyboardSizeDp * density;
            preferences.edit().putInt("keyboard_size", keyboardSizeDp).apply();
        } catch (NumberFormatException e) {
            Log.e(TAG, "Invalid keyboard size: " + e.getMessage());
            keyboardSizePx = defaultKbSizeDp * density;
            updatingKeyboardSize = true;
            ksizeEditText.setText(String.format(Locale.getDefault(), "%d", defaultKbSizeDp));
            ksizeEditText.setSelection(ksizeEditText.getText().length());
            updatingKeyboardSize = false;
        }
    }

    private int clampKeyboardSizeDp(int keyboardSizeDp) {
        // The full keyboard has four rows. Limit a key row to one sixth of the
        // shortest display side so rotation always leaves room for the game
        // surface, including row spacing and system insets.
        int shortestSidePx = Math.min(
                getResources().getDisplayMetrics().widthPixels,
                getResources().getDisplayMetrics().heightPixels);
        int maximumSizeDp = Math.max(
                defaultKbSizeDp,
                (int) Math.floor(shortestSidePx / density / 6.0f));
        return Math.max(0, Math.min(keyboardSizeDp, maximumSizeDp));
    }

    @Override
    public void afterTextChanged(Editable editable) {}

    @Override
    public void onCheckedChanged(CompoundButton compoundButton, boolean b) {
        fullScreen = b;
        preferences.edit().putBoolean("full_screen", fullScreen).apply();
    }

}
