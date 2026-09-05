package org.develz.crawl;

import android.content.Context;
import android.graphics.Color;
import android.util.AttributeSet;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.KeyEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;


public class DCSSKeyboard extends DCSSKeyboardBase implements View.OnClickListener {

    static final int MINIMUM_TOUCH_TARGET_DP = 48;
    public static final int CONTEXT_GAME = 0;
    public static final int CONTEXT_NAVIGATION = 1;
    public static final int CONTEXT_TEXT = 2;
    private int inputContext = -1;
    private int keyboardMode;
    private boolean manualFull;
    private final Button[] contextButtons = new Button[6];

    // Keyboards
    private final View keyboardLower;
    private final View keyboardUpper;
    private final View keyboardCtrl;
    private final View keyboardNumeric;
    private final View keyboardMobile;
    private final View compactToggle;

    // Constructors
    public DCSSKeyboard(Context context) {
        this(context, null, 0);
    }

    public DCSSKeyboard(Context context, AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public DCSSKeyboard(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);

        // Load layout
        LayoutInflater.from(context).inflate(R.layout.keyboard, this, true);

        // Keyboards
        keyboardLower = findViewById(R.id.keyboard_lower);
        keyboardUpper = findViewById(R.id.keyboard_upper);
        keyboardCtrl = findViewById(R.id.keyboard_ctrl);
        keyboardNumeric = findViewById(R.id.keyboard_numeric);
        keyboardMobile = findViewById(R.id.keyboard_mobile);
        compactToggle = findViewById(R.id.key_compact_lower);

        // Initialize key buttons - lower keyboard
        initKey(R.id.key_q);
        initKey(R.id.key_w);
        initKey(R.id.key_e);
        initKey(R.id.key_r);
        initKey(R.id.key_t);
        initKey(R.id.key_y);
        initKey(R.id.key_u);
        initKey(R.id.key_i);
        initKey(R.id.key_o);
        initKey(R.id.key_p);

        initKey(R.id.key_a);
        initKey(R.id.key_s);
        initKey(R.id.key_d);
        initKey(R.id.key_f);
        initKey(R.id.key_g);
        initKey(R.id.key_h);
        initKey(R.id.key_j);
        initKey(R.id.key_k);
        initKey(R.id.key_l);
        initKey(R.id.key_bspace);

        initKey(R.id.key_tab_lower);
        initKey(R.id.key_z);
        initKey(R.id.key_x);
        initKey(R.id.key_c);
        initKey(R.id.key_v);
        initKey(R.id.key_b);
        initKey(R.id.key_n);
        initKey(R.id.key_m);
        initKey(R.id.key_semicol);
        initKey(R.id.key_apos);

        initKey(R.id.key_shift_lower);
        initKey(R.id.key_ctrl_lower);
        initKey(R.id.key_grave);
        initKey(R.id.key_5);
        initKey(R.id.key_minus);
        initKey(R.id.key_plus);
        initKey(R.id.key_enter);
        initKey(R.id.key_compact_lower);
        initKey(R.id.key_123_lower);

        // Initialize buttons - upper keyboard
        initKey(R.id.key_Q);
        initKey(R.id.key_W);
        initKey(R.id.key_E);
        initKey(R.id.key_R);
        initKey(R.id.key_T);
        initKey(R.id.key_Y);
        initKey(R.id.key_U);
        initKey(R.id.key_I);
        initKey(R.id.key_O);
        initKey(R.id.key_P);

        initKey(R.id.key_A);
        initKey(R.id.key_S);
        initKey(R.id.key_D);
        initKey(R.id.key_F);
        initKey(R.id.key_G);
        initKey(R.id.key_H);
        initKey(R.id.key_J);
        initKey(R.id.key_K);
        initKey(R.id.key_L);
        initKey(R.id.key_equal);

        initKey(R.id.key_tab_upper);
        initKey(R.id.key_Z);
        initKey(R.id.key_X);
        initKey(R.id.key_C);
        initKey(R.id.key_V);
        initKey(R.id.key_B);
        initKey(R.id.key_N);
        initKey(R.id.key_M);
        initKey(R.id.key_colon);
        initKey(R.id.key_quot);

        initKey(R.id.key_shift_upper);
        initKey(R.id.key_ctrl_upper);
        initKey(R.id.key_lt);
        initKey(R.id.key_gt);
        initKey(R.id.key_comma);
        initKey(R.id.key_dot);
        initKey(R.id.key_space);
        initKey(R.id.key_123_upper);

        // Initialize buttons - ctrl keyboard
        initKey(R.id.key_Cq);
        initKey(R.id.key_Cw);
        initKey(R.id.key_Ce);
        initKey(R.id.key_Cr);
        initKey(R.id.key_Ct);
        initKey(R.id.key_Cy);
        initKey(R.id.key_Cu);
        initKey(R.id.key_Ci);
        initKey(R.id.key_Co);
        initKey(R.id.key_Cp);

        initKey(R.id.key_Ca);
        initKey(R.id.key_Cs);
        initKey(R.id.key_Cd);
        initKey(R.id.key_Cf);
        initKey(R.id.key_Cg);
        initKey(R.id.key_Ch);
        initKey(R.id.key_Cj);
        initKey(R.id.key_Ck);
        initKey(R.id.key_Cl);
        initKey(R.id.key_pipe);

        initKey(R.id.key_quest);
        initKey(R.id.key_Cz);
        initKey(R.id.key_Cx);
        initKey(R.id.key_Cc);
        initKey(R.id.key_Cv);
        initKey(R.id.key_Cb);
        initKey(R.id.key_Cn);
        initKey(R.id.key_Cm);
        initKey(R.id.key_slash);
        initKey(R.id.key_bslash);

        initKey(R.id.key_shift_ctrl);
        initKey(R.id.key_ctrl_ctrl);
        initKey(R.id.key_lcurly);
        initKey(R.id.key_rcurly);
        initKey(R.id.key_lbracket);
        initKey(R.id.key_rbracket);
        initKey(R.id.key_escape);
        initKey(R.id.key_123_ctrl);

        // Initialize buttons - numeric keyboard
        initKey(R.id.key_num_F1);
        initKey(R.id.key_num_F2);
        initKey(R.id.key_num_F3);
        initKey(R.id.key_num_tilde);
        initKey(R.id.key_num_exclam);
        initKey(R.id.key_num_at);
        initKey(R.id.key_num_hash);
        initKey(R.id.key_num_7);
        initKey(R.id.key_num_8);
        initKey(R.id.key_num_9);

        initKey(R.id.key_num_F4);
        initKey(R.id.key_num_F5);
        initKey(R.id.key_num_F6);
        initKey(R.id.key_num_dollar);
        initKey(R.id.key_num_percent);
        initKey(R.id.key_num_circum);
        initKey(R.id.key_num_amper);
        initKey(R.id.key_num_4);
        initKey(R.id.key_num_5);
        initKey(R.id.key_num_6);

        initKey(R.id.key_num_F7);
        initKey(R.id.key_num_F8);
        initKey(R.id.key_num_F9);
        initKey(R.id.key_num_aster);
        initKey(R.id.key_num_lparen);
        initKey(R.id.key_num_rparen);
        initKey(R.id.key_num_lowline);
        initKey(R.id.key_num_1);
        initKey(R.id.key_num_2);
        initKey(R.id.key_num_3);

        initKey(R.id.key_num_F10);
        initKey(R.id.key_num_F11);
        initKey(R.id.key_num_F12);
        initKey(R.id.key_num_lt);
        initKey(R.id.key_num_gt);
        initKey(R.id.key_num_equal);
        initKey(R.id.key_num_quest);
        initKey(R.id.key_num_0);
        initKey(R.id.key_abc);

        // Initialize buttons - mobile compact keyboard
        initKey(R.id.key_mobile_7);
        initKey(R.id.key_mobile_8);
        initKey(R.id.key_mobile_9);
        initKey(R.id.key_mobile_explore);
        initKey(R.id.key_mobile_autofight);
        initKey(R.id.key_mobile_4);
        initKey(R.id.key_mobile_5);
        initKey(R.id.key_mobile_6);
        initKey(R.id.key_mobile_inventory);
        initKey(R.id.key_mobile_pickup);
        initKey(R.id.key_mobile_1);
        initKey(R.id.key_mobile_2);
        initKey(R.id.key_mobile_3);
        initKey(R.id.key_mobile_menu);
        initKey(R.id.key_mobile_back);
        initKey(R.id.key_mobile_expand);
        int[] slots = {R.id.key_context_0, R.id.key_context_1, R.id.key_context_2,
                R.id.key_context_3, R.id.key_context_4, R.id.key_context_5};
        for (int i = 0; i < slots.length; ++i) {
            Button button = findViewById(slots[i]);
            contextButtons[i] = button;
            buttonList.add(button);
        }
    }

    // Extra init settings
    @Override
    public void initKeyboard(int keyboardOption, int size) {
        keyboardMode = keyboardOption;
        // The touch-first layout is the primary Android control surface, so
        // keep every target at least 48dp even when an older installation has
        // a smaller keyboard-size preference saved.
        int effectiveSize = size;
        if (keyboardOption == 4) {
            int minimumTouchTarget = Math.round(
                    MINIMUM_TOUCH_TARGET_DP * getResources().getDisplayMetrics().density);
            effectiveSize = Math.max(size, minimumTouchTarget);
        }
        super.initKeyboard(keyboardOption, effectiveSize);
        // Every full layout and the compact layout have exactly four rows.
        // Reserve that space even while child visibility changes, so the
        // activity's layout listener never resizes SDL for a layout switch.
        findViewById(R.id.main_layout).getLayoutParams().height = 4 * effectiveSize;
        if (keyboardOption == 2) {
            transparentKeyboard();
        } else if (keyboardOption == 4) {
            keyboardLower.setVisibility(View.GONE);
            keyboardUpper.setVisibility(View.GONE);
            keyboardCtrl.setVisibility(View.GONE);
            keyboardNumeric.setVisibility(View.GONE);
            keyboardMobile.setVisibility(View.VISIBLE);
            // RelativeLayout may keep the first inflated keyboard above later
            // siblings for touch dispatch even though the compact keyboard is
            // drawn last. Make the visible surface the actual hit-test front.
            keyboardMobile.bringToFront();
            compactToggle.setVisibility(View.VISIBLE);
        }
        if (keyboardOption == 1 || keyboardOption == 2) {
            compactToggle.setVisibility(View.VISIBLE);
        }
    }

    // Called on the Android UI thread. Repeated native input waits must not
    // override a user's manual choice of full/compact/numeric layout.
    // Screen values match ui::InputScreen. No translated text is an identity.
    private int contextLabelResource(int screen, int slot) {
        switch (screen) {
            case 1: // Inventory (including pickup)
                switch (slot) {
                    case 0: return R.string.ok;
                    case 1: return R.string.back;
                    case 2: return R.string.keyboard_previous_category;
                    case 3: return R.string.keyboard_next_category;
                    case 5: return R.string.keyboard_switch_action;
                }
                break;
            case 2: // Item description
            case 3: // Spell description
                if (slot == 1) return R.string.back;
                break;
            case 4: // Targeting
                switch (slot) {
                    case 0: return R.string.ok;
                    case 1: return R.string.cancel;
                    case 2: return R.string.keyboard_previous_target;
                    case 3: return R.string.keyboard_next_target;
                    case 4: return R.string.keyboard_self;
                }
                break;
            case 7: // Level map
                switch (slot) {
                    case 1: return R.string.back;
                    case 2: return R.string.keyboard_upstairs;
                    case 3: return R.string.keyboard_downstairs;
                    case 4: return R.string.keyboard_portals;
                    case 5: return R.string.keyboard_traps;
                }
                break;
        }
        return 0;
    }

    public void setInputContext(int context, int screen, String[] labels, int[] keys) {
        if (keyboardMode == 0 || keyboardMode == 3) {
            return;
        }
        Log.i("AndroidKeyboard", "context=" + context + " screen=" + screen
                + " manualFull=" + manualFull + " height=" + getHeight());
        for (int i = 0; i < contextButtons.length; ++i) {
            Button button = contextButtons[i];
            final int key = keys[i];
            String label = labels[i] == null ? "" : labels[i];
            if (key != 0 && label.isEmpty()) {
                int resource = contextLabelResource(screen, i);
                if (resource != 0) label = getResources().getString(resource);
            }
            boolean active = key != 0 && !label.isEmpty();
            button.setText(label);
            button.setContentDescription(label);
            button.setEnabled(active);
            button.setVisibility(active ? View.VISIBLE : View.INVISIBLE);
            button.setOnClickListener(active ? v -> sendContextKey(key) : null);
        }
        if (context == inputContext) {
            return;
        }
        inputContext = context;
        boolean gameplay = context == CONTEXT_GAME;
        Button explore = findViewById(R.id.key_mobile_explore);
        explore.setTag(Integer.toString(gameplay ? KeyEvent.KEYCODE_O : KeyEvent.KEYCODE_ENTER));
        explore.setText(gameplay ? R.string.keyboard_explore : R.string.ok);
        explore.setContentDescription(getResources().getString(
                gameplay ? R.string.keyboard_explore : R.string.ok));
        Button center = findViewById(R.id.key_mobile_5);
        center.setText(gameplay ? getResources().getString(R.string.keyboard_rest) : "5");
        center.setContentDescription(center.getText());
        for (int id : new int[] {R.id.key_mobile_autofight, R.id.key_mobile_inventory,
                R.id.key_mobile_pickup, R.id.key_mobile_menu}) {
            // Keep grid geometry stable while removing gameplay-only actions.
            findViewById(id).setVisibility(gameplay ? View.VISIBLE : View.INVISIBLE);
        }
        if (manualFull) {
            return;
        }
        keyboardUpper.setVisibility(View.GONE);
        keyboardCtrl.setVisibility(View.GONE);
        keyboardNumeric.setVisibility(View.GONE);
        boolean full = context == CONTEXT_TEXT || gameplay && keyboardMode != 4;
        keyboardLower.setVisibility(full ? View.VISIBLE : View.GONE);
        keyboardMobile.setVisibility(full ? View.GONE : View.VISIBLE);
        if (!full) {
            keyboardMobile.bringToFront();
        }
    }

    // Swap keyboards
    @Override
    protected void updateLayout(View v) {
        Log.i("AndroidKeyboard", "updateLayout key=" + v.getId()
                + " context=" + inputContext + " height=" + getHeight());
        if (v.getId() == R.id.key_mobile_expand) {
            manualFull = true;
            keyboardMobile.setVisibility(View.GONE);
            keyboardLower.setVisibility(View.VISIBLE);
        } else if (v.getId() == R.id.key_compact_lower) {
            manualFull = false;
            keyboardLower.setVisibility(View.GONE);
            keyboardUpper.setVisibility(View.GONE);
            keyboardCtrl.setVisibility(View.GONE);
            keyboardNumeric.setVisibility(View.GONE);
            keyboardMobile.setVisibility(View.VISIBLE);
            keyboardMobile.bringToFront();
        } else if ((v.getId() == R.id.key_shift_lower) ||
                (v.getId() == R.id.key_shift_ctrl)) {
            keyboardLower.setVisibility(View.GONE);
            keyboardCtrl.setVisibility(View.GONE);
            keyboardNumeric.setVisibility(View.GONE);
            keyboardMobile.setVisibility(View.GONE);
            keyboardUpper.setVisibility(View.VISIBLE);
        } else if (v.getId() == R.id.key_ctrl_lower ||
                v.getId() == R.id.key_ctrl_upper) {
            keyboardLower.setVisibility(View.GONE);
            keyboardUpper.setVisibility(View.GONE);
            keyboardNumeric.setVisibility(View.GONE);
            keyboardMobile.setVisibility(View.GONE);
            keyboardCtrl.setVisibility(View.VISIBLE);
        } else if ((v.getId() == R.id.key_123_lower) ||
                (v.getId() == R.id.key_123_upper) ||
                (v.getId() == R.id.key_123_ctrl)) {
            keyboardLower.setVisibility(View.GONE);
            keyboardUpper.setVisibility(View.GONE);
            keyboardCtrl.setVisibility(View.GONE);
            keyboardMobile.setVisibility(View.GONE);
            keyboardNumeric.setVisibility(View.VISIBLE);
        } else if ((v.getId() == R.id.key_abc) ||
                (((LinearLayout)v.getParent().getParent()).getId() == R.id.keyboard_upper) ||
                (((LinearLayout)v.getParent().getParent()).getId() == R.id.keyboard_ctrl)) {
            keyboardUpper.setVisibility(View.GONE);
            keyboardCtrl.setVisibility(View.GONE);
            keyboardNumeric.setVisibility(View.GONE);
            keyboardMobile.setVisibility(View.GONE);
            keyboardLower.setVisibility(View.VISIBLE);
        }
    }

    // Turn keyboard transparent
    private void transparentKeyboard() {
        RelativeLayout mainLayout = findViewById(R.id.main_layout);
        mainLayout.setBackgroundColor(Color.TRANSPARENT);
        for (Button button : buttonList) {
            button.setBackgroundResource(R.drawable.transparent_button);
        }
    }

}
