#ifdef USE_TILE_WEB
#pragma once

#include <string>
#include <vector>

class WebTextArea
{
public:
    WebTextArea(string name);
    virtual ~WebTextArea();

    void resize(int mx, int my);

    void clear();

    void put_character(char32_t chr, int fg, int bg, int x, int y);
    void put_string(const char32_t *str, int fg, int bg, int &x, int &y);

    void send(bool force = false);

    int mx, my; // Size

protected:
    char32_t *m_cbuf; // Character buffer
    uint8_t *m_abuf; // Color buffer

    char32_t *m_old_cbuf;
    uint8_t *m_old_abuf;

    // Zero-width suffixes belong to the preceding spacing glyph.
    std::vector<string> m_combining;
    std::vector<string> m_old_combining;

    string m_client_side_name;

    bool m_dirty;

    // Render one terminal row and update its last-sent snapshot.
    string render_line(int y, bool &dirty);

    virtual void on_resize();
};

#endif
