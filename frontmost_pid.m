#import <AppKit/AppKit.h>
#include <stdio.h>

int main(void) {
    @autoreleasepool {
        NSRunningApplication *frontmost = NSWorkspace.sharedWorkspace.frontmostApplication;
        if (frontmost == nil) {
            return 1;
        }
        printf("%d\n", frontmost.processIdentifier);
        return 0;
    }
}
