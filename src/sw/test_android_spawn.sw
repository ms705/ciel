foo = [];

foo[0] = *(spawn_exec("android", {"inputs": [], "jar_lib": "tests.jar", "class_name": "skywriting.examples.tests.android.TaskTest"}, 1)[0]);

for (i in range(1,9)) {
	foo[i] = *(spawn_exec("android", {"inputs": [], "jar_lib": "tests.jar", "class_name": "skywriting.examples.tests.android.TaskTest", "foo": i}, 1)[0]);
}

return foo;

