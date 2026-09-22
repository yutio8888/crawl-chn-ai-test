package org.develz.crawl;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.Color;
import android.os.Handler;
import android.os.Looper;
import android.util.AttributeSet;
import android.util.Log;
import android.view.HapticFeedbackConstants;
import android.view.LayoutInflater;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;

import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Set;


public class DCSSKeyboard extends DCSSKeyboardBase implements View.OnClickListener {

    static final int MINIMUM_TOUCH_TARGET_DP = 48;
    // Holding the compact auto-fight key keeps attacking without repeated
    // taps. One repeat per interval keeps the queue close to the game's own
    // pace, and the cap bounds a finger that never lifts.
    static final long AUTOFIGHT_REPEAT_INTERVAL_MS = 300;
    static final int AUTOFIGHT_MAX_REPEATS = 60;
    public static final int CONTEXT_GAME = 0;
    // ui::INPUT_MORE_KEY: CK_F10, which cio.h numbers down from
    // CK_F15 = -279 on every non-Windows build. Opens the native list of
    // the page's remaining actions.
    private static final int KEY_MORE = -274;
    public static final int CONTEXT_NAVIGATION = 1;
    public static final int CONTEXT_TEXT = 2;
    public static final int CONTEXT_NUMBER = 3;
    private int inputContext = -1;
    private final Handler autofightHandler = new Handler(Looper.getMainLooper());
    private int autofightRepeats;
    private int keyboardMode;
    private boolean manualFull;
    private View layoutBeforeText;
    private boolean manualFullBeforeText;
    private Runnable systemKeyboardAction;
    private final Button[] contextButtons = new Button[6];
    private final Map<Button, CharSequence> fixedLabels = new IdentityHashMap<>();
    private int requestedKeyHeight;
    private int configuredWidth = -1;

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
        initKey(R.id.key_system_keyboard);
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
        for (Button button : buttonList) {
            fixedLabels.put(button, button.getText());
        }
        int[] slots = {R.id.key_context_0, R.id.key_context_1, R.id.key_context_2,
                R.id.key_context_3, R.id.key_context_4, R.id.key_context_5};
        for (int i = 0; i < slots.length; ++i) {
            Button button = findViewById(slots[i]);
            contextButtons[i] = button;
            buttonList.add(button);
        }
        initAutofightRepeat();
    }

    // Auto-fight is the one compact action a player repeats many times in a
    // row, so let a long press hold it down instead of tapping per attack.
    @SuppressLint("ClickableViewAccessibility")
    private void initAutofightRepeat() {
        Button autofight = findViewById(R.id.key_mobile_autofight);
        autofight.setOnLongClickListener(v -> {
            v.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
            autofightRepeats = 0;
            repeatAutofight();
            return true;
        });
        // Returning false leaves the click and long-click handling intact;
        // this only observes the release that ends a repeat.
        autofight.setOnTouchListener((v, event) -> {
            int action = event.getActionMasked();
            if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
                stopAutofightRepeat();
            }
            return false;
        });
    }

    // Send one auto-fight key and schedule the next one, unless the hold has
    // reached the cap.
    private void repeatAutofight() {
        Button autofight = findViewById(R.id.key_mobile_autofight);
        onClick(autofight);
        long delay = autofightRepeatDelayMs(++autofightRepeats);
        if (delay >= 0) {
            autofightHandler.postDelayed(this::repeatAutofight, delay);
        }
    }

    // Delay before the repeat that follows `repeatsSoFar` sent keys, or -1
    // once the hold has produced enough of them.
    static long autofightRepeatDelayMs(int repeatsSoFar) {
        return repeatsSoFar < AUTOFIGHT_MAX_REPEATS ? AUTOFIGHT_REPEAT_INTERVAL_MS : -1;
    }

    private void stopAutofightRepeat() {
        autofightHandler.removeCallbacksAndMessages(null);
    }

    @Override
    protected void onDetachedFromWindow() {
        stopAutofightRepeat();
        super.onDetachedFromWindow();
    }

    // Extra init settings
    @Override
    public void initKeyboard(int keyboardOption, int size) {
        keyboardMode = keyboardOption;
        // The touch-first layout is the primary Android control surface, so
        // keep every target at least 48dp even when an older installation has
        // a smaller keyboard-size preference saved.
        int minimumTouchTarget = Math.round(
                MINIMUM_TOUCH_TARGET_DP * getResources().getDisplayMetrics().density);
        int effectiveSize = Math.max(size, minimumTouchTarget);
        requestedKeyHeight = effectiveSize;
        configuredWidth = -1;
        super.initKeyboard(keyboardOption, effectiveSize);
        // Initial reserve; onMeasure fits every layout to the configured width
        // and font metrics before the Activity observes the keyboard height.
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
        updateTextToolbar();
    }

    @Override
    public void refreshTextSizes() {
        super.refreshTextSizes();
        configuredWidth = -1;
    }

    public static boolean isTextContext(int context) {
        return context == CONTEXT_TEXT || context == CONTEXT_NUMBER;
    }

    public void setSystemKeyboardAction(Runnable action) {
        systemKeyboardAction = action;
    }

    private void requestSystemKeyboard() {
        if (isTextContext(inputContext) && systemKeyboardAction != null) {
            systemKeyboardAction.run();
        }
    }

    private View selectedLayout() {
        for (View layout : new View[] {keyboardLower, keyboardUpper, keyboardCtrl,
                keyboardNumeric, keyboardMobile}) {
            if (layout.getVisibility() == View.VISIBLE) return layout;
        }
        return keyboardLower;
    }

    private void showLayout(View selected) {
        for (View layout : new View[] {keyboardLower, keyboardUpper, keyboardCtrl,
                keyboardNumeric, keyboardMobile}) {
            layout.setVisibility(layout == selected ? View.VISIBLE : View.GONE);
        }
        selected.bringToFront();
        updateTextToolbar();
    }

    private void updateTextToolbar() {
        findViewById(R.id.full_layout_container).setVisibility(
                keyboardMobile.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE);
        findViewById(R.id.key_system_keyboard).setVisibility(
                isTextContext(inputContext) ? View.VISIBLE : View.INVISIBLE);
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        int width = MeasureSpec.getSize(widthMeasureSpec);
        if (requestedKeyHeight > 0 && width > 0 && width != configuredWidth) {
            fitKeyRows(width);
            configuredWidth = width;
        }
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
    }

    // Use TextView's real line breaking, font fallback and padding rather than
    // estimating a height from sp. A fixed width with an unrestricted height
    // measures every line even when the previous configuration used short keys.
    private int labelHeight(Button button, CharSequence label, int width) {
        CharSequence previous = button.getText();
        button.setText(label);
        button.measure(MeasureSpec.makeMeasureSpec(width, MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED));
        int height = button.getMeasuredHeight();
        button.setText(previous);
        return height;
    }

    private int fixedRowHeight(LinearLayout row, int width) {
        row.measure(MeasureSpec.makeMeasureSpec(width, MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED));
        int height = requestedKeyHeight;
        for (int i = 0; i < row.getChildCount(); ++i) {
            Button button = (Button) row.getChildAt(i);
            // Read the original label: retargeting Explore to OK must not
            // change geometry when entering a menu or targeting screen.
            height = Math.max(height, labelHeight(button, fixedLabels.get(button),
                    button.getMeasuredWidth()));
        }
        return height;
    }

    private Set<Integer> contextLabelResources() {
        Set<Integer> resources = new HashSet<>();
        // Exercise the existing label mapping over ui::InputScreen and its
        // printable/action keys, so all supported pages share one reserve.
        for (int screen = 0; screen <= 19; ++screen) {
            for (int slot = 0; slot < contextButtons.length; ++slot) {
                for (int key = 9; key <= 126; ++key) {
                    int resource = contextLabelResource(screen, slot, key);
                    if (resource != 0) resources.add(resource);
                }
            }
        }
        resources.add(R.string.keyboard_more);
        resources.add(R.string.cancel);
        resources.add(R.string.keyboard_system);
        resources.add(R.string.keyboard_skip_messages);
        return resources;
    }

    private int contextRowHeight(Set<Integer> resources, int width, int fullWidth) {
        int height = requestedKeyHeight;
        for (int resource : resources) {
            // MORE has only Continue and Skip; Skip occupies two thirds of
            // the existing row rather than stretching every game's key row.
            int labelWidth = resource == R.string.keyboard_skip_messages
                    ? 2 * fullWidth / 3 : width;
            height = Math.max(height, labelHeight(contextButtons[0],
                    getResources().getString(resource), labelWidth));
        }
        return height;
    }

    private void fitKeyRows(int width) {
        // XML's zero padding bypasses the AppCompat shape's transparent
        // insets. Reserve those insets explicitly so letters never spill off
        // the coloured key face. Do not use its additional default content
        // padding: the ten-column full keyboard needs the remaining width.
        int horizontalInset = getResources().getDimensionPixelSize(
                androidx.appcompat.R.dimen.abc_button_inset_horizontal_material);
        int verticalInset = getResources().getDimensionPixelSize(
                androidx.appcompat.R.dimen.abc_button_inset_vertical_material);
        for (Button button : buttonList) {
            button.setPadding(horizontalInset, verticalInset, horizontalInset, verticalInset);
        }
        LinearLayout[] layouts = {(LinearLayout) keyboardLower,
                (LinearLayout) keyboardUpper, (LinearLayout) keyboardCtrl,
                (LinearLayout) keyboardNumeric, (LinearLayout) keyboardMobile};
        int[][] heights = new int[layouts.length][4];
        for (int i = 0; i < layouts.length; ++i) {
            LinearLayout layout = layouts[i];
            int rows = layout == keyboardMobile ? 3 : 4;
            for (int row = 0; row < rows; ++row) {
                heights[i][row] = fixedRowHeight((LinearLayout) layout.getChildAt(row), width);
            }
        }
        // Explore is also the persistent confirm key outside GAME.
        Button explore = findViewById(R.id.key_mobile_explore);
        int[] mobileHeights = heights[layouts.length - 1];
        mobileHeights[0] = Math.max(mobileHeights[0], labelHeight(explore,
                getResources().getString(R.string.ok), explore.getMeasuredWidth()));

        Set<Integer> resources = contextLabelResources();
        int contextHeight = contextRowHeight(resources, width / 6, width);
        int twoLines = labelHeight(contextButtons[0], "M\nM", width / 6);
        int columns = contextHeight > Math.max(requestedKeyHeight, twoLines) ? 3 : 6;
        if (columns == 3) {
            contextHeight = contextRowHeight(resources, width / 3, width);
        }
        LinearLayout first = findViewById(R.id.keyboard_context_first);
        LinearLayout second = findViewById(R.id.keyboard_context_second);
        for (int i = 0; i < contextButtons.length; ++i) {
            Button button = contextButtons[i];
            LinearLayout destination = i < columns ? first : second;
            if (button.getParent() != destination) {
                ((ViewGroup) button.getParent()).removeView(button);
                destination.addView(button);
            }
        }
        second.setVisibility(columns == 3 ? View.VISIBLE : View.GONE);
        int contextRows = contextButtons.length / columns;
        mobileHeights[3] = contextRows * contextHeight;
        first.getLayoutParams().height = contextHeight;
        second.getLayoutParams().height = contextHeight;
        for (Button button : contextButtons) {
            button.getLayoutParams().height = ViewGroup.LayoutParams.MATCH_PARENT;
        }
        int fullHeight = 0;
        int mobileHeight = 0;
        for (int i = 0; i < layouts.length; ++i) {
            LinearLayout layout = layouts[i];
            int rows = layout == keyboardMobile ? 3 : 4;
            for (int row = 0; row < rows; ++row) {
                LinearLayout keyRow = (LinearLayout) layout.getChildAt(row);
                for (int key = 0; key < keyRow.getChildCount(); ++key) {
                    keyRow.getChildAt(key).getLayoutParams().height = heights[i][row];
                }
            }
            int height = heights[i][0] + heights[i][1] + heights[i][2] + heights[i][3];
            if (layout == keyboardMobile) mobileHeight = height;
            else fullHeight = Math.max(fullHeight, height);
        }
        Button systemKeyboard = findViewById(R.id.key_system_keyboard);
        int toolbarHeight = Math.max(requestedKeyHeight,
                labelHeight(systemKeyboard, fixedLabels.get(systemKeyboard), width));
        systemKeyboard.getLayoutParams().height = toolbarHeight;
        findViewById(R.id.full_keys_layout).getLayoutParams().height = fullHeight;
        findViewById(R.id.keyboard_context_rows).getLayoutParams().height = mobileHeights[3];
        // Keep the native surface stable, without combining the tallest row
        // from each different layout into an unnecessarily large keyboard.
        findViewById(R.id.main_layout).getLayoutParams().height =
                Math.max(mobileHeight, fullHeight + toolbarHeight);
    }

    // Called on the Android UI thread. Repeated native input waits must not
    // override a user's manual choice of full/compact/numeric layout.
    // Screen values match ui::InputScreen. No translated text is an identity.
    // Slot-based tables come first; pages whose slots hold different keys per
    // situation resolve by the game key instead.
    private int contextLabelResource(int screen, int slot, int key) {
        switch (screen) {
            case 1: // Inventory (including pickup)
                if (key == '-') return R.string.keyboard_known_toggle;
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
            case 5: // Confirmation
                if (slot == 2) return R.string.keyboard_always;
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
            case 8: // Use-item menus (wield, wear, quaff, read, evoke, ...)
                switch (key) {
                    case '!': return R.string.keyboard_switch_action;
                    case '?': return R.string.keyboard_describe;
                    case ',': return R.string.keyboard_switch_list;
                    case '-': return R.string.keyboard_unarmed;
                }
                break;
            case 9: // Shop
                switch (key) {
                    case '!': return R.string.keyboard_switch_action;
                    case '/': return R.string.keyboard_sort;
                    case '$': return R.string.keyboard_shopping_list;
                }
                break;
            case 10: // Generic menus with a mode cycle, help or sorting
                switch (key) {
                    case '/': return R.string.keyboard_sort;
                    case '=': return R.string.keyboard_filter_useless;
                    case '-': return R.string.keyboard_more_info;
                }
                break;
            case 11: // Monster and generic descriptions
            case 12: // God description and join
                switch (key) {
                    case '!': return R.string.keyboard_cycle_pane;
                    case 13: return R.string.keyboard_join;
                }
                break;
            case 13: // Feature description
                switch (key) {
                    case '<': return R.string.keyboard_go_up;
                    case '>': return R.string.keyboard_go_down;
                    case '[':
                    case ']': return R.string.keyboard_view_destination;
                    case 'o': return R.string.keyboard_open_door;
                    case 'c': return R.string.keyboard_close_door;
                }
                break;
            case 14: // Skills
                switch (key) {
                    case '=': return R.string.keyboard_set_target;
                    case '-': return R.string.keyboard_clear_target;
                    case '!': return R.string.keyboard_cycle_view;
                    case '*': return R.string.keyboard_all_skills;
                }
                break;
            case 15: // Interlevel travel prompt
                switch (key) {
                    case 9: return R.string.keyboard_default_target;
                    case '*': return R.string.keyboard_waypoints;
                    case '_': return R.string.keyboard_altars;
                }
                break;
            case 16: // Display layer toggles
                switch (key) {
                    case 'a': return R.string.keyboard_layers_all;
                    case 'm': return R.string.keyboard_layers_monsters;
                    case 'p': return R.string.keyboard_layers_player;
                    case 'i': return R.string.keyboard_layers_items;
                    case 'c': return R.string.keyboard_layers_clouds;
                }
                break;
            case 17: // Quiver action selection
                switch (key) {
                    case '*': return R.string.keyboard_inventory;
                    case '&': return R.string.keyboard_all_spells;
                    case '^': return R.string.keyboard_all_abilities;
                    case '-': return R.string.keyboard_clear_quiver;
                }
                break;
            case 18: // Ordinary dungeon commands; keys follow the live bindings
                switch (slot) {
                    case 0: return R.string.keyboard_rest;
                    case 1: return R.string.keyboard_quaff;
                    case 2: return R.string.keyboard_read;
                    case 3: return R.string.keyboard_fire;
                    case 4: return R.string.keyboard_cast;
                    case 5: return R.string.keyboard_ability;
                }
                break;
            case 19: // Shout and ally orders prompt
                switch (key) {
                    case 't': return R.string.keyboard_shout;
                    case 'a': return R.string.keyboard_order_attack;
                    case 'r': return R.string.keyboard_order_retreat;
                    case 's': return R.string.keyboard_order_stop;
                    case 'g': return R.string.keyboard_order_guard;
                    case 'f': return R.string.keyboard_order_follow;
                }
                break;
        }
        switch (key) {
            case KEY_MORE: return R.string.keyboard_more;
            case 13: return R.string.ok;
            case 27: return R.string.back;
            case '!': return R.string.keyboard_cycle_mode;
            case '?': return R.string.keyboard_help;
        }
        return 0;
    }

    public void setInputContext(int context, int screen, String[] labels, int[] keys) {
        if (keyboardMode == 0 || keyboardMode == 3) {
            return;
        }
        Log.i("AndroidKeyboard", "context=" + context + " screen=" + screen
                + " manualFull=" + manualFull + " height=" + getHeight());
        boolean text = isTextContext(context);
        boolean wasText = isTextContext(inputContext);
        boolean more = screen == 6 && keys[2] == 0 && keys[3] == 0
                && keys[4] == 0 && keys[5] == 0;
        for (int i = 0; i < contextButtons.length; ++i) {
            Button button = contextButtons[i];
            final int key = keys[i];
            String label = labels[i] == null ? "" : labels[i];
            if (key != 0 && label.isEmpty()) {
                int resource = contextLabelResource(screen, i, key);
                if (resource != 0) label = getResources().getString(resource);
            }
            boolean active = key != 0 && !label.isEmpty();
            button.setText(label);
            button.setContentDescription(label);
            button.setEnabled(active);
            button.setVisibility(active ? View.VISIBLE
                    : more ? View.GONE : View.INVISIBLE);
            ((LinearLayout.LayoutParams) button.getLayoutParams()).weight = more && i == 1 ? 2 : 1;
            button.setOnClickListener(active ? v -> sendContextKey(key) : null);
        }
        if (text) {
            setTextAction(contextButtons[0], R.string.ok, () -> sendContextKey(13));
            setTextAction(contextButtons[1], R.string.cancel, () -> sendContextKey(27));
            setTextAction(contextButtons[2], R.string.keyboard_system, this::requestSystemKeyboard);
        }
        boolean gameplay = context == CONTEXT_GAME;
        if (!gameplay) {
            // A menu, prompt or targeting screen ends the allowed range for a
            // held auto-fight: further keys would answer that screen instead.
            stopAutofightRepeat();
        }
        if (context == inputContext) {
            return;
        }
        inputContext = context;
        retarget(R.id.key_mobile_explore,
                gameplay ? KeyEvent.KEYCODE_O : KeyEvent.KEYCODE_ENTER,
                getResources().getString(gameplay ? R.string.keyboard_explore : R.string.ok));
        // In the dungeon the centre of the pad waits one turn (CMD_WAIT via
        // '.'); resting lives in the action row. Every other context keeps
        // numpad 5 so menus, targeting and the level map see their usual key.
        retarget(R.id.key_mobile_5,
                gameplay ? KeyEvent.KEYCODE_PERIOD : KeyEvent.KEYCODE_NUMPAD_5,
                gameplay ? getResources().getString(R.string.keyboard_wait) : "5");
        for (int id : new int[] {R.id.key_mobile_autofight, R.id.key_mobile_inventory,
                R.id.key_mobile_pickup, R.id.key_mobile_menu}) {
            // Keep grid geometry stable while removing gameplay-only actions.
            findViewById(id).setVisibility(gameplay ? View.VISIBLE : View.INVISIBLE);
        }
        if (text && !wasText) {
            layoutBeforeText = selectedLayout();
            manualFullBeforeText = manualFull;
            // The entry is visible immediately even if the previous manual
            // layout was numeric, Ctrl or uppercase.
            showLayout(keyboardLower);
            return;
        }
        if (!text && wasText && layoutBeforeText != null) {
            manualFull = manualFullBeforeText;
            showLayout(layoutBeforeText);
            layoutBeforeText = null;
            return;
        }
        if (manualFull) {
            return;
        }
        keyboardUpper.setVisibility(View.GONE);
        keyboardCtrl.setVisibility(View.GONE);
        keyboardNumeric.setVisibility(View.GONE);
        boolean full = text || gameplay && keyboardMode != 4;
        keyboardLower.setVisibility(full ? View.VISIBLE : View.GONE);
        keyboardMobile.setVisibility(full ? View.GONE : View.VISIBLE);
        if (!full) {
            keyboardMobile.bringToFront();
        }
        updateTextToolbar();
    }

    private void setTextAction(Button button, int label, Runnable action) {
        button.setText(label);
        button.setContentDescription(button.getText());
        button.setVisibility(View.VISIBLE);
        button.setEnabled(true);
        button.setOnClickListener(v -> action.run());
    }

    // A fixed button whose key and label follow the input context.
    private void retarget(int id, int keycode, CharSequence label) {
        Button button = findViewById(id);
        button.setTag(Integer.toString(keycode));
        button.setText(label);
        button.setContentDescription(label);
    }

    // Swap keyboards
    @Override
    protected void updateLayout(View v) {
        if (v.getId() != R.id.key_mobile_autofight) {
            stopAutofightRepeat();
        }
        Log.i("AndroidKeyboard", "updateLayout key=" + v.getId()
                + " context=" + inputContext + " height=" + getHeight());
        if (v.getId() == R.id.key_system_keyboard) {
            requestSystemKeyboard();
            return;
        } else if (v.getId() == R.id.key_mobile_expand) {
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
        updateTextToolbar();
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
