/* Pixel backgrounds for the GTKLock 5 module API. Authentication stays in GTKLock. */
#include <gtk/gtk.h>
#include <gmodule.h>
#include <math.h>

G_MODULE_EXPORT guint module_major_version = 5;
G_MODULE_EXPORT guint module_minor_version = 0;

#define WIDTH 1280.0
#define HEIGHT 720.0
#define TAU (2.0 * G_PI)

enum Pattern { RAIN, BREEZE, WAVES, ORBITS, FIREFLIES, RIPPLES, CHECKER,
               SPIRAL, SCAN, BOUNCE, PATTERN_COUNT };

struct Point { double x, y, phase, speed; };
static struct Point points[100];
static enum Pattern pattern;
static gint64 started;
static gboolean dark;

static double wrap(double coordinate, double span) {
    return coordinate - floor(coordinate / span) * span;
}

static double reflect(double coordinate, double span) {
    return span - fabs(wrap(coordinate, span * 2) - span);
}

static void pixel(cairo_t *cr, double x, double y, int size, gboolean pink) {
    if (fabs(x - WIDTH / 2) < 145 && fabs(y - HEIGHT / 2) < 155)
        return;
    if (pink)
        cairo_set_source_rgb(cr, dark ? .80 : .69, dark ? .54 : .39, dark ? .64 : .50);
    else
        cairo_set_source_rgb(cr, dark ? .55 : .42, dark ? .55 : .42, dark ? .55 : .42);
    cairo_rectangle(cr, round(x), round(y), size, size);
    cairo_fill(cr);
}

static void render(cairo_t *cr, double time) {
    static const double centers[][2] = {{220, 185}, {1050, 180}, {235, 535}, {1035, 535}};
    switch (pattern) {
    case RAIN:
        for (int i = 0; i < 100; i++)
            pixel(cr, points[i].x, wrap(points[i].y + time * points[i].speed, HEIGHT), 2 + i % 3, FALSE);
        break;
    case BREEZE:
        for (int i = 0; i < 36; i++)
            for (int j = 0; j < 4; j++)
                pixel(cr, wrap(points[i].x + time * 30 - j * 8, WIDTH),
                      points[i].y + 12 * sin(time / 3 + points[i].phase), 4 - j, j == 0);
        break;
    case WAVES:
        for (int band = 0; band < 5; band++)
            for (int x = 20; x < WIDTH; x += 19)
                pixel(cr, x, 84 + band * 136 + 22 * sin(x / 76.0 - time * .8 + band * .6),
                      4 - band % 2, band % 2 == 0);
        break;
    case ORBITS:
        for (int i = 0; i < 4; i++)
            for (int ring = 1; ring <= 3; ring++)
                for (int j = 0; j < ring * 5; j++) {
                    double angle = points[i].phase + time * (ring % 2 ? -1 : 1) / (2 + ring / 2.0)
                                   + TAU * j / (ring * 5);
                    pixel(cr, centers[i][0] + ring * 35 * cos(angle), centers[i][1] + ring * 25 * sin(angle),
                          j % 3 == 0 ? 4 : 2, j % 3 == 0);
                }
        break;
    case FIREFLIES:
        for (int i = 0; i < 85; i++) {
            double glow = (1 + sin(points[i].phase + time * (0.45 + i % 10 * .05))) / 2;
            if (glow > .4)
                pixel(cr, points[i].x, points[i].y, (int)round(2 + 4 * glow), glow > .8);
        }
        break;
    case RIPPLES:
        for (int i = 0; i < 4; i++)
            for (int ring = 0; ring < 3; ring++) {
                double radius = 12 + wrap(points[i].phase * 8 + time * 12 + ring * 49, 145);
                for (int j = 0; j < 36; j++) {
                    double angle = TAU * j / 36;
                    pixel(cr, centers[i][0] + radius * cos(angle), centers[i][1] + radius * sin(angle),
                          3, ring == 1);
                }
            }
        break;
    case CHECKER:
        for (int row = 1; row < 16; row++)
            for (int col = 1; col < 29; col++)
                if ((row + col) % 2 == 0) {
                    double level = wrap(col - row - time * 2, 8);
                    int size = (int)round(2 + fmax(0, 4 - 2 * fmin(level, 8 - level)));
                    pixel(cr, col * 44, row * 44, size, size >= 4);
                }
        break;
    case SPIRAL:
        for (int arm = 0; arm < 4; arm++)
            for (int step = 9; step < 37; step++) {
                double angle = arm * TAU / 4 + step * .13 + time * .24;
                pixel(cr, WIDTH / 2 + step * 16 * cos(angle),
                      HEIGHT / 2 + step * 9 * sin(angle), 4, step % 3 == 0);
            }
        break;
    case SCAN:
        for (int y = 28; y < HEIGHT; y += 27) {
            for (int x = 45; x < WIDTH; x += 85)
                pixel(cr, x, y, 2, FALSE);
            for (int j = 0; j < 5; j++)
                pixel(cr, wrap(time * 33 + points[0].x - j * 13, WIDTH), y, 5 - j, j < 2);
        }
        break;
    case BOUNCE:
        for (int i = 0; i < 25; i++)
            for (int j = 3; j >= 0; j--) {
                double t = time - j * .23;
                pixel(cr, reflect(points[i].x + cos(points[i].phase) * points[i].speed * t, WIDTH),
                      reflect(points[i].y + sin(points[i].phase) * points[i].speed * t, HEIGHT), 5 - j, j == 0);
            }
        break;
    default:
        break;
    }
}

static gboolean draw_background(GtkWidget *area, cairo_t *cr, gpointer data) {
    (void)data;
    double paper = dark ? 23.0 / 255 : 1;
    double time = (g_get_monotonic_time() - started) / (double)G_USEC_PER_SEC;
    cairo_set_source_rgb(cr, paper, paper, paper);
    cairo_paint(cr);
    cairo_scale(cr, gtk_widget_get_allocated_width(area) / WIDTH,
                gtk_widget_get_allocated_height(area) / HEIGHT);
    cairo_set_antialias(cr, CAIRO_ANTIALIAS_NONE);
    render(cr, time);
    return FALSE;
}

static gboolean tick(GtkWidget *area, GdkFrameClock *clock, gpointer data) {
    gint64 *previous = data;
    gint64 frame = (gdk_frame_clock_get_frame_time(clock) - started) * 30 / G_USEC_PER_SEC;
    if (frame != *previous) {
        *previous = frame;
        gtk_widget_queue_draw(area);
    }
    return G_SOURCE_CONTINUE;
}

G_MODULE_EXPORT void on_activation(gpointer lock, int index) {
    (void)lock;
    (void)index;
    started = g_get_monotonic_time();
    pattern = g_random_int_range(0, PATTERN_COUNT);
    dark = g_strcmp0(g_getenv("PAPERBIT_LOCK_DARK"), "1") == 0;
    for (guint i = 0; i < G_N_ELEMENTS(points); i++) {
        points[i] = (struct Point){g_random_double_range(0, WIDTH), g_random_double_range(0, HEIGHT),
                                  g_random_double_range(0, TAU), g_random_double_range(16, 50)};
    }
}

static void hide_password_icon(GtkEntry *entry, GParamSpec *property, gpointer data) {
    (void)property;
    (void)data;
    if (gtk_entry_get_icon_storage_type(entry, GTK_ENTRY_ICON_SECONDARY) != GTK_IMAGE_EMPTY)
        gtk_entry_set_icon_from_icon_name(entry, GTK_ENTRY_ICON_SECONDARY, NULL);
}

static void style_unlock_form(GtkWidget *widget, gpointer data) {
    (void)data;
    const char *name = gtk_widget_get_name(widget);
    if (g_str_equal(name, "input-label") || g_str_equal(name, "unlock-button")) {
        gtk_widget_set_no_show_all(widget, TRUE);
        gtk_widget_hide(widget);
    } else if (GTK_IS_ENTRY(widget) && g_str_equal(name, "input-field")) {
        GtkEntry *entry = GTK_ENTRY(widget);
        gtk_widget_set_size_request(widget, 320, 52);
        gtk_entry_set_icon_activatable(entry, GTK_ENTRY_ICON_SECONDARY, FALSE);
        hide_password_icon(entry, NULL, NULL);
        /* GTKLock restores the eye when focus moves to another monitor. */
        g_signal_connect(entry, "notify::secondary-icon-name", G_CALLBACK(hide_password_icon), NULL);
    }
    if (GTK_IS_CONTAINER(widget))
        gtk_container_foreach(GTK_CONTAINER(widget), style_unlock_form, NULL);
}

G_MODULE_EXPORT void on_window_create(gpointer lock, gpointer window) {
    (void)lock;
    (void)window;
    /* Use GTK's public widget tree rather than GTKLock's private window struct. */
    GList *windows = gtk_window_list_toplevels();
    for (GList *it = windows; it; it = it->next) {
        if (!GTK_IS_APPLICATION_WINDOW(it->data))
            continue;
        GtkWidget *overlay = gtk_bin_get_child(GTK_BIN(it->data));
        if (!GTK_IS_OVERLAY(overlay) || g_object_get_data(G_OBJECT(overlay), "paperbit-pattern"))
            continue;
        GtkWidget *form = gtk_bin_get_child(GTK_BIN(overlay));
        if (!form)
            continue;
        style_unlock_form(form, NULL);
        GtkWidget *area = gtk_drawing_area_new();
        g_object_set_data(G_OBJECT(overlay), "paperbit-pattern", area);
        g_object_ref(form);
        gtk_container_remove(GTK_CONTAINER(overlay), form);
        gtk_container_add(GTK_CONTAINER(overlay), area);
        gtk_overlay_add_overlay(GTK_OVERLAY(overlay), form);
        g_object_unref(form);
        g_signal_connect(area, "draw", G_CALLBACK(draw_background), NULL);
        gtk_widget_add_tick_callback(area, tick, g_new0(gint64, 1), g_free);
    }
    g_list_free(windows);
}
