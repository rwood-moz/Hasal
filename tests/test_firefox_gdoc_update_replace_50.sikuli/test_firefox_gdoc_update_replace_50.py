# if you are putting your test script folders under {git project folder}/tests/, it will work fine.
# otherwise, you either add it to system path before you run or hard coded it in here.
sys.path.append(sys.argv[2])
import browser
import common
import gdoc

com = common.General()
ff = browser.Firefox()
gd = gdoc.gDoc()

ff.clickBar()
ff.enterLink(sys.argv[3])
sleep(5)
gd.wait_for_loaded()

type(Key.END, Key.CTRL)
wait(0.3)
type(Key.UP, Key.SHIFT)
wait(0.3)
type(Key.UP, Key.SHIFT)
wait(0.3)
type(Key.UP, Key.SHIFT)
wait(0.3)
type(Key.UP, Key.SHIFT)

gd.bold()

com.page_end()

sleep(2)
gd.deFoucsContentWindow()