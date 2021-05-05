function getSingleColorAngles(array) {
            var ret = [];
            for (var angle = 0; angle <= 180; angle++) {
                // check to see if the entire array is the same color
                var singlearr = getSingleDimensionalArray(array, angle).map(function(a) {
                    return a.join();// convert colors to strings (sorting multidimensional arrays is SLOW)
                });
                // simple case -- the arrays are 100% identical
                if (singlearr[0] === singlearr[singlearr.length - 1]) {
                    ret.push(angle);
                }
                else {
                    // slow case -- compare all unique color values with a threshold
                    var uniquevals = uniqueArray(singlearr);
                    var first = uniquevals[0];
                    for (var i = 1; i < uniquevals.length; i++) {
                        if (!colorsEqual(first, uniquevals[i])) {
                            break;
                        }
                        else {
                            if (i === uniquevals.length - 1) {
                                ret.push(angle);
                            }
                        }
                    }
                }
            }

            return ret;
        }