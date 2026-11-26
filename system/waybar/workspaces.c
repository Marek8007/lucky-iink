/* Keep each Waybar workspace tile a single pointer target on GTK 3. */
#include <gtk/gtk.h>
#include <gmodule.h>

static gboolean on_map(GSignalInvocationHint *hint, guint count,
                       const GValue *values, gpointer data) {
    (void)hint;
    (void)count;
    (void)data;
    GtkWidget *widget = g_value_get_object(&values[0]);
    if (!GTK_IS_BUTTON(widget) ||
        !gtk_style_context_has_class(gtk_widget_get_style_context(widget), "taskbar-window"))
        return TRUE;

    /* The app image stays visible. The workspace button handles hover and clicks. */
    GdkWindow *window = gtk_button_get_event_window(GTK_BUTTON(widget));
    if (window)
        gdk_window_set_pass_through(window, TRUE);
    return TRUE;
}

G_MODULE_EXPORT void gtk_module_init(gint *argc, gchar ***argv) {
    (void)argc;
    (void)argv;
    gpointer widget_class = g_type_class_ref(GTK_TYPE_WIDGET);
    guint map_signal = g_signal_lookup("map", GTK_TYPE_WIDGET);
    g_signal_add_emission_hook(map_signal, 0, on_map, NULL, NULL);
    g_type_class_unref(widget_class);
}
