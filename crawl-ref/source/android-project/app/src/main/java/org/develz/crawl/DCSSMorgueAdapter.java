package org.develz.crawl;

import android.content.res.Resources;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.CheckedTextView;

import androidx.recyclerview.widget.RecyclerView;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;

public class DCSSMorgueAdapter extends RecyclerView.Adapter<DCSSMorgueAdapter.ViewHolder> {

    private File[] morgueFiles;
    private File selectedFile;

    private OnMorgueListener morgueListener;

    // Constructor
    public DCSSMorgueAdapter(File morgueDir, OnMorgueListener morgueListener) {
        if (!morgueDir.exists()) {
            if (!morgueDir.mkdir()) {
                Log.e(DCSSLauncher.TAG, "Can't create folder "+morgueDir.getPath());
            }
        }
        this.morgueFiles = morgueDir.listFiles();
        if (morgueFiles == null) morgueFiles = new File[0];
        this.morgueListener = morgueListener;
    }

    // Single element in the RecyclerView
    public static class ViewHolder extends RecyclerView.ViewHolder implements View.OnClickListener, View.OnFocusChangeListener {
        private final LinearLayout layout;
        private final CheckedTextView nameView;
        private final TextView timeView;
        private OnMorgueListener morgueListener;

        public ViewHolder(View view, OnMorgueListener morgueListener) {
            super(view);
            layout = view.findViewById(R.id.layout);
            nameView = view.findViewById(R.id.fileName);
            timeView = view.findViewById(R.id.fileTime);
            view.setOnClickListener(this);
            view.setOnFocusChangeListener(this);
            this.morgueListener = morgueListener;
        }

        public LinearLayout getLayout() {
            return layout;
        }

        public TextView getNameView() {
            return nameView;
        }

        public TextView getTimeView() {
            return timeView;
        }

        @Override
        public void onClick(View v) {
            int position = getBindingAdapterPosition();
            if (position != RecyclerView.NO_POSITION) this.morgueListener.onMorgueClick(position);
        }

        @Override
        public void onFocusChange(View view, boolean b) {
            Resources resources = getNameView().getResources();
            int color = view.isActivated()
                    ? (view.isFocused() ? R.color.dark_green_focused : R.color.dark_green)
                    : (view.isFocused() ? R.color.black_focused : R.color.black);
            getLayout().setBackgroundColor(resources.getColor(color));
        }
    }

    // Used by the layout manager to render each element in the RecyclerView
    @Override
    public ViewHolder onCreateViewHolder(ViewGroup viewGroup, int viewType) {
        View view = LayoutInflater.from(viewGroup.getContext())
                .inflate(R.layout.morgue_file, viewGroup, false);
        return new ViewHolder(view, morgueListener);
    }

    // Replace the contents of a view (invoked by the layout manager)
    @Override
    public void onBindViewHolder(ViewHolder viewHolder, final int position) {
        viewHolder.getNameView().setText(morgueFiles[position].getName());
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        Date modifiedDate = new Date(morgueFiles[position].lastModified());
        viewHolder.getTimeView().setText(dateFormat.format(modifiedDate));
        boolean selected = morgueFiles[position].equals(selectedFile);
        viewHolder.itemView.setSelected(selected);
        viewHolder.itemView.setActivated(selected);
        viewHolder.nameView.setChecked(selected);
        viewHolder.itemView.setContentDescription(morgueFiles[position].getName()
                + ", " + dateFormat.format(modifiedDate));
        viewHolder.onFocusChange(viewHolder.itemView, viewHolder.itemView.isFocused());
    }

    // Return the size of your dataset (invoked by the layout manager)
    @Override
    public int getItemCount() {
        if (morgueFiles == null) {
            return 0;
        } else {
            return morgueFiles.length;
        }
    }

    // order 0: Number asc.
    // order 1: Number desc.
    // order 2: Time asc.
    // order 3: Time asc.
    public void sortMorgueFiles(int order) {
        int modifier = (order % 2 == 0) ? 1 : -1;
        if (order < 2) {
            Arrays.sort(morgueFiles, (a, b) -> a.getName().compareToIgnoreCase(b.getName())*modifier);
        } else {
            Arrays.sort(morgueFiles, (a, b) -> Long.compare(a.lastModified(), b.lastModified())*modifier);
        }
        notifyDataSetChanged();
    }

    public File getMorgueFile(int position) {
        if (position >= 0 && position < morgueFiles.length) {
            return morgueFiles[position];
        } else {
            return null;
        }
    }

    public void setSelectedPosition(int position) {
        File file = getMorgueFile(position);
        if (file != null && !file.equals(selectedFile)) {
            File previous = selectedFile;
            selectedFile = file;
            for (int i = 0; i < morgueFiles.length; ++i) {
                if (morgueFiles[i].equals(previous)) notifyItemChanged(i);
            }
            notifyItemChanged(position);
        }
    }

    public interface OnMorgueListener{
        void onMorgueClick(int position);
    }

}
