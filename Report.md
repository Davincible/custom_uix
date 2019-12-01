---


---

<h1 id="static-code-analysis-of-mimikatz-and-sqlite3">Static code analysis of Mimikatz (and SQLite3)</h1>
<p>December 1st, University of Twente - Software Security</p>
<p>David Brouwer ( s2193698 )</p>
<h2 id="mimikatz">Mimikatz</h2>
<p>Mimikatz is a security tool developed in C to audit Windows security. It is well known for its ability to extract passwords and hashes on a Windows system. Mimikatz can, for example, extract a password from memory, and build Golden tickets for the Kerobos Golden ticket attack.</p>
<h3 id="development">Development</h3>
<p>It can be found on <a href="http://github.com/gentilkiwi/mimikatz">github.com/gentilkiwi/mimikatz</a>, and is almost exclusively developed by the GitHub user <a href="https://github.com/gentilkiwi">gentilkiwi</a>. The Frenchman <a href="https://www.linkedin.com/in/delpy/">Benjamin Delphy</a> is the mastermind behind this account and is currently a security researcher at the Bank of France.</p>
<p>As of today, Mimikatz over 8.7k stars, and over 2k forks.</p>
<h2 id="code-analysis">Code analysis</h2>
<p>The code base has been analysed with the tool <a href="http://cppcheck.sourceforge.net/">cppcheck</a> to perform static code analysis. The analysis has been performed on the cloned version from github with the command:</p>
<p><code>cppcheck $(find . | grep -E "\.c$|\.h$") --enable=all --force 2&gt; report.txt</code></p>
<p>The file paths have been directly supplied with the <code>find</code> command to assert it would include all relevant files. This way it is possible to observe beforehand which files will be scanned, to make sure all the files are included. This was the fastest and easiest method that gave me the confidence that all appropriate files were scanned, rather than including all the sperate directories.</p>
<p>Subsequently, the ‘stderr’ is redirected to a file with file descriptor 2. This stores only the output of the scan in a file. By using this file descriptor option, the first file descriptor, ‘stdout’, containing the information on the progress of the scan, will not be saved in the report, as this is irrelevant information for the processing of the results.</p>
<h3 id="scan-results">Scan results</h3>
<p>Cppcheck provides various output levels, such as “error”, “warning”, “style” and “information”. For the complete scan, more than 1000 items were detected. As the intention is to find more security-related issues, only the “error” and “warning” messages will be processed. These results can be filtered out by loading the report into a vim buffer and deleting all other lines with <code>:g!/(error)\|(warning)/d</code>. The result can be found in Appendix A.</p>
<p>Upon investigating the report, it is apparent that the majority of the findings are in the file “modules/sqlite3_omit.c”. This is not code of Mimikatz itself, but merely an external module added to the codebase for portability. As the header of the file states, “This file is an amalgamation of many separate C source files from SQLite version 3.27.2.”. All individual .c files are merged into a single file with more than 220.000 lines of code. Among these errors in this file, there are two interesting errors in the security context:</p>
<pre><code>
[modules/sqlite3_omit.c:22845]: (error) Memory leak: p

[modules/sqlite3_omit.c:22910]: (error) Common realloc mistake: 'p' nulled but not freed upon failure

</code></pre>
<p>As the messages reports, cppcheck identified a memory leak for the first error. The relevant code block is:</p>
<pre class=" language-c"><code class="prism  language-c">
<span class="token keyword">static</span>  <span class="token keyword">void</span>  <span class="token operator">*</span><span class="token function">sqlite3MemMalloc</span><span class="token punctuation">(</span><span class="token keyword">int</span>  nByte<span class="token punctuation">)</span><span class="token punctuation">{</span>

<span class="token macro property">#<span class="token directive keyword">ifdef</span>  SQLITE_MALLOCSIZE</span>

<span class="token keyword">void</span>  <span class="token operator">*</span>p<span class="token punctuation">;</span>

<span class="token function">testcase</span><span class="token punctuation">(</span>  <span class="token function">ROUND8</span><span class="token punctuation">(</span>nByte<span class="token punctuation">)</span><span class="token operator">==</span>nByte  <span class="token punctuation">)</span><span class="token punctuation">;</span>

p  <span class="token operator">=</span>  <span class="token function">SQLITE_MALLOC</span><span class="token punctuation">(</span>  nByte  <span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token keyword">if</span><span class="token punctuation">(</span>  p<span class="token operator">==</span><span class="token number">0</span>  <span class="token punctuation">)</span><span class="token punctuation">{</span>

<span class="token function">testcase</span><span class="token punctuation">(</span>  sqlite3GlobalConfig<span class="token punctuation">.</span>xLog<span class="token operator">!=</span><span class="token number">0</span>  <span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token function">sqlite3_log</span><span class="token punctuation">(</span>SQLITE_NOMEM<span class="token punctuation">,</span> <span class="token string">"failed to allocate %u bytes of memory"</span><span class="token punctuation">,</span> nByte<span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token punctuation">}</span>

<span class="token keyword">return</span>  p<span class="token punctuation">;</span>

<span class="token macro property">#<span class="token directive keyword">else</span></span>

sqlite3_int64  <span class="token operator">*</span>p<span class="token punctuation">;</span>

<span class="token function">assert</span><span class="token punctuation">(</span>  nByte<span class="token operator">&gt;</span><span class="token number">0</span>  <span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token function">testcase</span><span class="token punctuation">(</span>  <span class="token function">ROUND8</span><span class="token punctuation">(</span>nByte<span class="token punctuation">)</span><span class="token operator">!=</span>nByte  <span class="token punctuation">)</span><span class="token punctuation">;</span>

p  <span class="token operator">=</span>  <span class="token function">SQLITE_MALLOC</span><span class="token punctuation">(</span>  nByte<span class="token operator">+</span><span class="token number">8</span>  <span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token keyword">if</span><span class="token punctuation">(</span>  p  <span class="token punctuation">)</span><span class="token punctuation">{</span>

p<span class="token punctuation">[</span><span class="token number">0</span><span class="token punctuation">]</span> <span class="token operator">=</span>  nByte<span class="token punctuation">;</span>

p<span class="token operator">++</span><span class="token punctuation">;</span>

<span class="token punctuation">}</span><span class="token keyword">else</span><span class="token punctuation">{</span>

<span class="token function">testcase</span><span class="token punctuation">(</span>  sqlite3GlobalConfig<span class="token punctuation">.</span>xLog<span class="token operator">!=</span><span class="token number">0</span>  <span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token function">sqlite3_log</span><span class="token punctuation">(</span>SQLITE_NOMEM<span class="token punctuation">,</span> <span class="token string">"failed to allocate %u bytes of memory"</span><span class="token punctuation">,</span> nByte<span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token punctuation">}</span>

<span class="token keyword">return</span>  <span class="token punctuation">(</span><span class="token keyword">void</span>  <span class="token operator">*</span><span class="token punctuation">)</span>p<span class="token punctuation">;</span>

<span class="token macro property">#<span class="token directive keyword">endif</span></span>

<span class="token punctuation">}</span>

</code></pre>
<p>Cppcheck indicates that there is a memory leak in this function at the last return statement. If we look at the code in the else clause of the “SQLITE_MALLOCSIZE” check, we can see that the code tries to allocate a certain amount of memory with <code>SQLITE_MALLOC</code>, and then returns the dereferenced variable p. If the memory is allocated correctly, this is fine as the memory holds data stored there by the program itself. However, if it fails the data at that location in memory can be arbitrary, creating a memory leak. To mitigate this issue, the return statement could be placed inside the <code>if( p )</code> statement to make sure p is allocated, and either return a specific value on failure, or no value at all.</p>
<p>Secondly, for the realloc error the relevant code block is:</p>
<pre class=" language-c"><code class="prism  language-c">
p <span class="token operator">=</span>  <span class="token function">SQLITE_REALLOC</span><span class="token punctuation">(</span>p<span class="token punctuation">,</span> nByte<span class="token operator">+</span><span class="token number">8</span> <span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token keyword">if</span><span class="token punctuation">(</span> p <span class="token punctuation">)</span><span class="token punctuation">{</span>

p<span class="token punctuation">[</span><span class="token number">0</span><span class="token punctuation">]</span> <span class="token operator">=</span> nByte<span class="token punctuation">;</span>

p<span class="token operator">++</span><span class="token punctuation">;</span>

<span class="token punctuation">}</span><span class="token keyword">else</span><span class="token punctuation">{</span>

<span class="token function">testcase</span><span class="token punctuation">(</span> sqlite3GlobalConfig<span class="token punctuation">.</span>xLog<span class="token operator">!=</span><span class="token number">0</span> <span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token function">sqlite3_log</span><span class="token punctuation">(</span>SQLITE_NOMEM<span class="token punctuation">,</span>

<span class="token string">"failed memory resize %u to %u bytes"</span><span class="token punctuation">,</span>

<span class="token function">sqlite3MemSize</span><span class="token punctuation">(</span>pPrior<span class="token punctuation">)</span><span class="token punctuation">,</span> nByte<span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token punctuation">}</span>

</code></pre>
<p>According to the cppcheck error, there should be an extra line with <code>free(p);</code> in the else clause of the if statement to fix this. However, as realloc tries to copy over the data to a new and bigger allocated memory block, it might still be desirable to use the data in p, even if the allocated size is only the original size. Calling free on p in that case would destroy that data.</p>
<h2 id="conclusion">Conclusion</h2>
<p>The errors discussed here are in the sqlite3 module, of the Mimikatz codebase, and not in the Mimikatz code itself. While I did start by performing static code analysis of Mimikatz, I ended up dissecting error messages of the SQLite3 code. However, as Mimikatz makes use of this module, it could introduce errors in the Mimikatz program itself, and any other program that uses SQLite3, which are a lot. As for the first error, the data in the address of the memory leak upon failure of malloc is random, and not directly user-controlled. Thus, the only danger is undefined behaviour depending on what happens with the pointer, and no direct attack. Therefore, I would rate the severity of the bug as LOW, if it even is a bug, as I find it hard to imagine that the SQLite team would oversee such a simple memory leak reported by static analysis. And for the second error, whether it actually is a bug is debatable, and depends on the implementation of the developers. The last commit to the sqlite3 module file in the Mimikatz repository was 8 months ago, and the header of the file identifies the code as version 3.27.2. Currently, the latest release of SQLite3 is 3.30.1 according to their <a href="https://www.sqlite.org/index.html">website</a>. Although, if by taking a look at the latest amalgamation, the code relating both errors is still the same as in version 3.27.2. The error has been reported to the SQLite team, see <a href="https://ibb.co/JRqj1TY">this link</a> for a screenshot of the email.</p>
<h2 id="appendix-a---error-and-warning-results-from-cppcheck">Appendix A - error and warning results from cppcheck</h2>
<pre><code>
[inc/Fci.h:488]: (error) syntax error

[inc/NTSecPKG.h:628]: (error) syntax error

[mimikatz/modules/crypto/kuhl_m_crypto_extractor.c:654]: (error) syntax error

[mimikatz/modules/crypto/kuhl_m_crypto_sc.c:137]: (error) Uninitialized variable: aVendor

[mimikatz/modules/crypto/kuhl_m_crypto_sc.c:147]: (error) Uninitialized variable: aModel

[mimikatz/modules/dpapi/kuhl_m_dpapi_oe.c:210] -&gt; [mimikatz/modules/dpapi/kuhl_m_dpapi_oe.c:208]: (warning) Either the condition 'if(entry)' is redundant or there is possible null pointer dereference: entry.

[mimikatz/modules/kuhl_m_minesweeper.c:142]: (error) Unmatched '}'. Configuration: ''.

[mimikatz/modules/lsadump/kuhl_m_lsadump_dc.c:2660] -&gt; [mimikatz/modules/lsadump/kuhl_m_lsadump_dc.c:2638] -&gt; [mimikatz/modules/lsadump/kuhl_m_lsadump_dc.c:2659]: (error) Non-local variable 'pDCShadowDomainInfoInUse' will use pointer to local variable 'DCShadowDomainInfo'.

[mimikatz/modules/lsadump/kuhl_m_lsadump_dc.c:1342]: (error) Uninitialized variable: dwErr

[mimikatz/modules/sekurlsa/crypto/kuhl_m_sekurlsa_nt5.c:103]: (error) Unmatched '}'. Configuration: ''.

[mimikatz/modules/sekurlsa/crypto/kuhl_m_sekurlsa_nt6.c:205]: (error) Unmatched '}'. Configuration: ''.

[modules/kull_m_busylight.c:236] -&gt; [modules/kull_m_busylight.c:246]: (warning) Either the condition 'device' is redundant or there is possible null pointer dereference: device.

[modules/kull_m_busylight.c:254] -&gt; [modules/kull_m_busylight.c:271]: (warning) Either the condition 'device' is redundant or there is possible null pointer dereference: device.

[modules/kull_m_crypto.c:1074] -&gt; [modules/kull_m_crypto.c:1073]: (warning) Either the condition 'if(dh&amp;&amp;publicKey)' is redundant or there is possible null pointer dereference: dh.

[modules/kull_m_dpapi.c:739] -&gt; [modules/kull_m_dpapi.c:738]: (warning) Either the condition 'if(sid)' is redundant or there is possible null pointer dereference: sid.

[modules/kull_m_rdm.c:111]: (warning) Redundant code: Found a statement that begins with string constant.

[modules/kull_m_string.c:424]: (error) va_list 'args' was opened but not closed by va_end().

[modules/sqlite3_omit.c:95911]: (warning) Assert statement calls a function which may have desired side effects: 'sqlite3ExprIsInteger'.

[modules/sqlite3_omit.c:98727]: (warning) Assert statement calls a function which may have desired side effects: 'sqlite3GetInt32'.

[modules/sqlite3_omit.c:113744]: (warning) Assert statement calls a function which may have desired side effects: 'sqlite3_value_blob'.

[modules/sqlite3_omit.c:113864]: (warning) Assert statement calls a function which may have desired side effects: 'sqlite3_value_blob'.

[modules/sqlite3_omit.c:156738]: (warning) Assert statement modifies 'x'.

[modules/sqlite3_omit.c:20762]: (error) Address of local auto-variable assigned to a function parameter.

[modules/sqlite3_omit.c:20804]: (error) Address of local auto-variable assigned to a function parameter.

[modules/sqlite3_omit.c:125321]: (error) Address of local auto-variable assigned to a function parameter.

[modules/sqlite3_omit.c:131119]: (error) Address of local auto-variable assigned to a function parameter.

[modules/sqlite3_omit.c:134537]: (error) Address of local auto-variable assigned to a function parameter.

[modules/sqlite3_omit.c:69920]: (error) Array 'pCArray-&gt;apEnd[6]' accessed at index 6, which is out of bounds.

[modules/sqlite3_omit.c:69945]: (error) Array 'pCArray-&gt;ixNx[6]' accessed at index 6, which is out of bounds.

[modules/sqlite3_omit.c:70004]: (error) Array 'pCArray-&gt;apEnd[6]' accessed at index 6, which is out of bounds.

[modules/sqlite3_omit.c:70032]: (error) Array 'pCArray-&gt;ixNx[6]' accessed at index 6, which is out of bounds.

[modules/sqlite3_omit.c:149187] -&gt; [modules/sqlite3_omit.c:149197]: (warning) Either the condition 'j&lt;(int)(sizeof(yy_lookahead)/sizeof(yy_lookahead[0]))' is redundant or the array 'yy_action[1385]' is accessed at index 1539, which is out of bounds.

[modules/sqlite3_omit.c:114590] -&gt; [modules/sqlite3_omit.c:114590]: (error) The address of local variable 'likeInfoAlt' is accessed at non-zero index.

[modules/sqlite3_omit.c:114591] -&gt; [modules/sqlite3_omit.c:114591]: (error) The address of local variable 'likeInfoAlt' is accessed at non-zero index.

[modules/sqlite3_omit.c:60786] -&gt; [modules/sqlite3_omit.c:60834]: (warning) Identical condition 'rc', second condition is always false

[modules/sqlite3_omit.c:22845]: (error) Memory leak: p

[modules/sqlite3_omit.c:22910]: (error) Common realloc mistake: 'p' nulled but not freed upon failure

[modules/sqlite3_omit.c:78006]: (warning) Possible null pointer dereference: apSub

[modules/sqlite3_omit.c:78007]: (warning) Possible null pointer dereference: apSub

[modules/sqlite3_omit.c:78009]: (warning) Possible null pointer dereference: apSub

[modules/sqlite3_omit.c:78031]: (warning) Possible null pointer dereference: pSub

[modules/sqlite3_omit.c:78032]: (warning) Possible null pointer dereference: pSub

[modules/sqlite3_omit.c:99406] -&gt; [modules/sqlite3_omit.c:99391]: (warning) Either the condition 'pEList!=0' is redundant or there is possible null pointer dereference: pEList.

[modules/sqlite3_omit.c:26704]: (error) Overflow in pointer arithmetic, NULL pointer is subtracted.

[modules/sqlite3_omit.c:53044] -&gt; [modules/sqlite3_omit.c:53043]: (warning) Either the condition '!pMaster' is redundant or there is pointer arithmetic with NULL pointer.

[modules/sqlite3_omit.c:150783]: (warning) Redundant assignment of 'yymsp[0].minor.yy182' to itself.

[modules/sqlite3_omit.c:59090] -&gt; [modules/sqlite3_omit.c:59253] -&gt; [modules/sqlite3_omit.c:59091] -&gt; [modules/sqlite3_omit.c:59254] -&gt; [modules/sqlite3_omit.c:59254]: (error) Subtracting pointers that point to different objects

[modules/sqlite3_omit.c:108258]: (warning) Size of pointer 'zExtra' used instead of size of its data.

[modules/sqlite3_omit.c:144323]: (warning) Suspicious code: sign conversion of 'nTabList-1' in calculation, even though 'nTabList-1' can have a negative value

[modules/sqlite3_omit.c:80505]: (warning) Assert statement calls a function which may have desired side effects: 'vdbeRecordCompareDebug'.

[modules/sqlite3_omit.c:80526]: (warning) Assert statement calls a function which may have desired side effects: 'vdbeRecordCompareDebug'.

[modules/sqlite3_omit.c:80633]: (warning) Assert statement calls a function which may have desired side effects: 'vdbeRecordCompareDebug'.

[modules/sqlite3_omit.c:80692]: (warning) Assert statement calls a function which may have desired side effects: 'vdbeRecordCompareDebug'.

[modules/sqlite3_omit.c:106726]: (warning) Assert statement calls a function which may have desired side effects: 'sqlite3VdbeAssertMayAbort'.

[modules/sqlite3_omit.c:149936]: (warning) %d in format string (no. 2) requires 'int' but the argument type is 'unsigned int'.

[modules/sqlite3_omit.c:149940]: (warning) %d in format string (no. 2) requires 'int' but the argument type is 'unsigned int'.

[modules/sqlite3_omit.c:56155] -&gt; [modules/sqlite3_omit.c:56154]: (warning) Either the condition 'pPg!=0' is redundant or there is possible null pointer dereference: pPg.

[modules/sqlite3_omit.c:48380]: (error) Array 'a[32]' accessed at index 9998, which is out of bounds.

[modules/sqlite3_omit.c:69920]: (error) Array 'pCArray-&gt;apEnd[6]' accessed at index 9999, which is out of bounds.

[modules/sqlite3_omit.c:69945]: (error) Array 'pCArray-&gt;ixNx[6]' accessed at index 9999, which is out of bounds.

[modules/sqlite3_omit.c:70004]: (error) Array 'pCArray-&gt;apEnd[6]' accessed at index 9999, which is out of bounds.

[modules/sqlite3_omit.c:70032]: (error) Array 'pCArray-&gt;ixNx[6]' accessed at index 9999, which is out of bounds.

[modules/sqlite3_omit.c:210611]: (warning) Assert statement calls a function which may have desired side effects: 'sqlite3_step'.

[modules/sqlite3_omit.c:201045]: (warning) %d in format string (no. 2) requires 'int' but the argument type is 'unsigned int'.

[modules/sqlite3_omit.c:201049]: (warning) %d in format string (no. 2) requires 'int' but the argument type is 'unsigned int'.

[modules/sqlite3_omit.c:24152]: (warning) %d in format string (no. 1) requires 'int' but the argument type is 'unsigned int'.

[modules/sqlite3_omit.c:24161]: (warning) %d in format string (no. 1) requires 'int' but the argument type is 'unsigned int'.

[modules/sqlite3_omit.c:24168]: (warning) %d in format string (no. 1) requires 'int' but the argument type is 'unsigned int'.

[modules/sqlite3_omit.c:24169]: (warning) %d in format string (no. 1) requires 'int' but the argument type is 'unsigned int'.

[modules/sqlite3_omit.c:24170]: (warning) %d in format string (no. 1) requires 'int' but the argument type is 'unsigned int'.

[modules/sqlite3_omit.c:191525] -&gt; [modules/sqlite3_omit.c:191543]: (warning) Either the condition 'pRbu' is redundant or there is possible null pointer dereference: pRbu.

[modules/sqlite3_omit.c:136445]: (error) Uninitialized variable: iReg

[modules/sqlite3_omit.c:40027]: (warning) Assignment of function parameter has no effect outside the function. Did you forget dereferencing it?

[modules/sqlite3_omit.c:62]: (error) failed to expand 'CTIMEOPT_VAL2', Wrong number of parameters for macro 'CTIMEOPT_VAL2_'.

[modules/sqlite3_omit.c:174746] -&gt; [modules/sqlite3_omit.c:174743]: (warning) Shifting 64-bit value by 64 bits is undefined behaviour. See condition at line 174746.

[modules/sqlite3_omit.c:48970] -&gt; [modules/sqlite3_omit.c:48984]: (warning) Either the condition '!p' is redundant or there is possible null pointer dereference: p.

[modules/sqlite3_omit.c:48970] -&gt; [modules/sqlite3_omit.c:48985]: (warning) Either the condition '!p' is redundant or there is possible null pointer dereference: p.

[modules/sqlite3_omit.c:48970] -&gt; [modules/sqlite3_omit.c:48986]: (warning) Either the condition '!p' is redundant or there is possible null pointer dereference: p.

[modules/sqlite3_omit.c:48970] -&gt; [modules/sqlite3_omit.c:48987]: (warning) Either the condition '!p' is redundant or there is possible null pointer dereference: p.

[modules/sqlite3_omit.c:97503]: (error) Uninitialized variable: p

[modules/sqlite3_omit.c:131777] -&gt; [modules/sqlite3_omit.c:131761]: (warning) Either the condition 'pTable!=0' is redundant or there is possible null pointer dereference: pTable.

</code></pre>

