// Debug overlay share sheet (ticket M0-UNITY-04). Debug builds only:
// Assets/Editor/Build/BuildInfoHook.cs keeps this file out of release builds
// (PluginImporter include-in-build delegate), matching the overlay assembly.
#import <UIKit/UIKit.h>

extern UIViewController* UnityGetGLViewController();

extern "C" void GJ_ShareFile(const char* path)
{
    if (path == NULL)
        return;
    NSString* file = [NSString stringWithUTF8String:path];
    NSURL* url = [NSURL fileURLWithPath:file];
    dispatch_async(dispatch_get_main_queue(), ^{
        UIViewController* root = UnityGetGLViewController();
        if (root == nil)
            return;
        UIActivityViewController* sheet =
            [[UIActivityViewController alloc] initWithActivityItems:@[ url ] applicationActivities:nil];
        // iPad presents the sheet as a popover anchored to the top-right corner (the overlay).
        UIPopoverPresentationController* popover = sheet.popoverPresentationController;
        if (popover != nil)
        {
            popover.sourceView = root.view;
            CGRect b = root.view.bounds;
            popover.sourceRect = CGRectMake(CGRectGetMaxX(b) - 1, CGRectGetMinY(b) + 1, 1, 1);
        }
        [root presentViewController:sheet animated:YES completion:nil];
    });
}
